from datetime import datetime
from typing import Annotated, AsyncGenerator

from sqlalchemy import DateTime, func
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

from app.config import get_db_url, get_docker_db_url

DATABASE_URL = get_docker_db_url()

engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

# настройка аннотаций
int_pk = Annotated[int, mapped_column(primary_key=True)]
# created_at = Annotated[DateTime(timezone=True), server_default=func.now()]
# updated_at = Annotated[DateTime(timezone=True), server_default=func.now(), onupdate=func.now()]
str_uniq = Annotated[str, mapped_column(unique=True, nullable=False)]
str_null_true = Annotated[str, mapped_column(nullable=True)]


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        return f'{cls.__name__.lower()}s'

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
