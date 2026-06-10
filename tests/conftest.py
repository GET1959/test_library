"""Pytest fixtures: тестовая БД в Postgres, миграции, чистка таблиц между тестами.

Подход: поднимаем отдельный Postgres в Docker (см. docker-compose.test.yml),
прогоняем Alembic до head, перед каждым тестом делаем TRUNCATE
borrows/books/authors/users — это быстрее, чем пересоздавать схему на каждый тест.

BorrowDAO.create_borrow / close_borrow используют app.database.async_session_maker,
поэтому в фикстуре мы подменяем этот модуль на тестовый session_maker.
"""
import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Тестовая БД собирается из POSTGRES_TEST_* ещё до импорта app.database,
# чтобы продовый engine в app.database.py не перехватил прод-URL.
os.environ.setdefault("POSTGRES_TEST_HOST", "localhost")
os.environ.setdefault("POSTGRES_TEST_PORT", "5433")
os.environ.setdefault("POSTGRES_TEST_USER", "postgres")
os.environ.setdefault("POSTGRES_TEST_PASSWORD", "postgres")
os.environ.setdefault("POSTGRES_TEST_DB", "mobile_library_test")

TEST_DATABASE_URL = (
    f"postgresql+asyncpg://{os.environ['POSTGRES_TEST_USER']}:"
    f"{os.environ['POSTGRES_TEST_PASSWORD']}@"
    f"{os.environ['POSTGRES_TEST_HOST']}:"
    f"{os.environ['POSTGRES_TEST_PORT']}/"
    f"{os.environ['POSTGRES_TEST_DB']}"
)

# Свой engine и свой session_maker — BorrowDAO всё равно использует
# app.database.async_session_maker, но мы его подменим в фикстуре monkeypatch.
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_maker = async_sessionmaker(test_engine, expire_on_commit=False)

# Тут импортируем app — после установки env.
# При импорте app.database создаст продовый engine, но мы его не используем в тестах.
from app.database import Base  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    """Один event loop на сессию, чтобы engine не закрывался между тестами."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _prepare_database():
    """Прогон Alembic до head один раз за сессию."""
    import asyncio
    import alembic.config
    import alembic.command
    from app import database as app_database

    # alembic/env.py делает `from app.database import DATABASE_URL` при каждом запуске,
    # поэтому патчим модуль до вызова upgrade, а не только cfg.
    original_url = app_database.DATABASE_URL
    app_database.DATABASE_URL = TEST_DATABASE_URL

    cfg = alembic.config.Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)

    try:
        # alembic/env.py вызывает asyncio.run() — нельзя звать из работающего loop.
        # Запускаем в отдельном потоке, где своего loop нет.
        await asyncio.to_thread(alembic.command.upgrade, cfg, "head")
    finally:
        app_database.DATABASE_URL = original_url

    yield

    await test_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _patch_session_maker(monkeypatch):
    """Подменяем async_session_maker во всех модулях, которые импортируют его напрямую.

    from-import создаёт локальную привязку, поэтому патча только app.database недостаточно —
    нужно патчить каждый модуль, где стоит `from app.database import async_session_maker`.
    """
    from app import database as app_database
    import app.core.base as base_module
    import app.books.core as books_core_module

    monkeypatch.setattr(app_database, "async_session_maker", test_session_maker)
    monkeypatch.setattr(base_module, "async_session_maker", test_session_maker)
    monkeypatch.setattr(books_core_module, "async_session_maker", test_session_maker)
    yield


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_maker() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def _truncate_tables(db_session: AsyncSession):
    """Чистим таблицы перед каждым тестом. Авто‑use, не надо подключать руками."""
    # Сначала borrows (FK на books/users), потом книги, авторов, пользователей.
    await db_session.execute(
        text("TRUNCATE TABLE borrows, books, authors, users RESTART IDENTITY CASCADE")
    )
    await db_session.commit()
    yield
