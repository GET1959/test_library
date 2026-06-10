"""Тесты BorrowDAO.create_borrow и BorrowDAO.close_borrow.

Что покрываем:
  * create_borrow: уменьшает quantity_to_borrow, создаёт Borrow с сегодняшней датой.
  * create_borrow: при quantity_to_borrow=0 — InsufficientCopiesError.
  * create_borrow: при двух параллельных выдачах с quantity=1 — только одна успешна
    (атомарность условного UPDATE).
  * close_borrow: проставляет return_date и инкрементит quantity_to_borrow.
  * close_borrow: повторное закрытие — BorrowNotFoundOrAlreadyClosedError.

Принцип: пишем ровно столько, чтобы атомарность была покрыта без зависимостей от
внутренностей Pydantic-схем и авторизации (тестируем DAO, не HTTP-слой).
"""
import asyncio
from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.books.core import (
    BorrowDAO,
    InsufficientCopiesError,
    BorrowNotFoundOrAlreadyClosedError,
)
from app.books.models import Book, Borrow
from app.authors.models import Author
from app.auth.models import User


# ---------- хелперы фикстур ----------

@pytest_asyncio.fixture
async def author(db_session) -> Author:
    a = Author(
        first_name="Александр",
        last_name="Пушкин",
        date_of_birth=date(1799, 6, 6),
    )
    db_session.add(a)
    await db_session.commit()
    await db_session.refresh(a)
    return a


@pytest_asyncio.fixture
async def book_factory(db_session, author):
    """Фабрика книг: book_factory(qty=2) -> Book c id и quantity_to_borrow=qty."""
    created: list[Book] = []

    async def _make(qty: int = 1, title: str = "Капитанская дочка") -> Book:
        b = Book(
            title=title,
            description="Повесть",
            author_id=author.id,
            quantity_to_borrow=qty,
        )
        db_session.add(b)
        await db_session.commit()
        await db_session.refresh(b)
        created.append(b)
        return b

    return _make


@pytest_asyncio.fixture
async def user_factory(db_session):
    """Фабрика пользователей с уже захешированным паролем (заглушка)."""
    from passlib.context import CryptContext

    pwd = CryptContext(schemes=["argon2"], deprecated="auto")
    created: list[User] = []

    async def _make(username: str = "tester", email: str = "t@e.x") -> User:
        u = User(
            username=username,
            email=email,
            hashed_password=pwd.hash("dummy-password"),
            is_active=True,
        )
        db_session.add(u)
        await db_session.commit()
        await db_session.refresh(u)
        created.append(u)
        return u

    return _make


# ---------- тесты create_borrow ----------

@pytest.mark.asyncio
async def test_create_borrow_decrements_quantity_and_creates_record(
    db_session, book_factory, user_factory
):
    book = await book_factory(qty=2)
    user = await user_factory()

    borrow = await BorrowDAO.create_borrow(book_id=book.id, user_id=user.id)

    assert isinstance(borrow, Borrow)
    assert borrow.book_id == book.id
    assert borrow.user_id == user.id
    assert borrow.return_date is None
    assert borrow.issue_date == date.today()

    refreshed = await db_session.get(Book, book.id, populate_existing=True)
    assert refreshed.quantity_to_borrow == 1, "остаток должен уменьшиться на 1"


@pytest.mark.asyncio
async def test_create_borrow_raises_when_no_copies(db_session, book_factory, user_factory):
    book = await book_factory(qty=0)
    user = await user_factory()

    with pytest.raises(InsufficientCopiesError):
        await BorrowDAO.create_borrow(book_id=book.id, user_id=user.id)

    # Проверяем, что в БД не появилось записей о выдаче и остаток не ушёл в минус.
    refreshed = await db_session.get(Book, book.id, populate_existing=True)
    assert refreshed.quantity_to_borrow == 0

    result = await db_session.execute(select(Borrow))
    assert result.scalars().all() == []


@pytest.mark.asyncio
async def test_create_borrow_concurrent_only_one_wins(
    db_session, book_factory, user_factory
):
    """При quantity=1 два параллельных запроса → ровно одна успешная выдача.

    Это и есть проверка атомарности условного UPDATE в create_borrow.
    """
    book = await book_factory(qty=1)
    u1 = await user_factory(username="u1", email="u1@e.x")
    u2 = await user_factory(username="u2", email="u2@e.x")

    # gather запускает оба корутина конкурентно в одном event loop.
    results = await asyncio.gather(
        BorrowDAO.create_borrow(book_id=book.id, user_id=u1.id),
        BorrowDAO.create_borrow(book_id=book.id, user_id=u2.id),
        return_exceptions=True,
    )

    successes = [r for r in results if isinstance(r, Borrow)]
    failures = [r for r in results if isinstance(r, InsufficientCopiesError)]

    assert len(successes) == 1, f"должна пройти ровно одна выдача, получили: {results}"
    assert len(failures) == 1, "вторая выдача обязана бросить InsufficientCopiesError"

    # Остаток — 0, а не -1.
    refreshed = await db_session.get(Book, book.id, populate_existing=True)
    assert refreshed.quantity_to_borrow == 0


# ---------- тесты close_borrow ----------

@pytest.mark.asyncio
async def test_close_borrow_sets_return_date_and_increments_quantity(
    db_session, book_factory, user_factory
):
    book = await book_factory(qty=1)
    user = await user_factory()

    borrow = await BorrowDAO.create_borrow(book_id=book.id, user_id=user.id)
    assert (await db_session.get(Book, book.id, populate_existing=True)).quantity_to_borrow == 0

    closed = await BorrowDAO.close_borrow(instance_id=borrow.id)

    assert closed.return_date == date.today()

    refreshed = await db_session.get(Book, book.id, populate_existing=True)
    assert refreshed.quantity_to_borrow == 1, "после возврата остаток должен вырасти на 1"


@pytest.mark.asyncio
async def test_close_borrow_twice_raises(db_session, book_factory, user_factory):
    book = await book_factory(qty=1)
    user = await user_factory()

    borrow = await BorrowDAO.create_borrow(book_id=book.id, user_id=user.id)
    await BorrowDAO.close_borrow(instance_id=borrow.id)

    with pytest.raises(BorrowNotFoundOrAlreadyClosedError):
        await BorrowDAO.close_borrow(instance_id=borrow.id)


@pytest.mark.asyncio
async def test_close_borrow_unknown_id_raises(db_session):
    with pytest.raises(BorrowNotFoundOrAlreadyClosedError):
        await BorrowDAO.close_borrow(instance_id=999_999)
