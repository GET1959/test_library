from datetime import date
from typing import Any, Optional

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from app.core.base import BaseDAO
from app.database import async_session_maker
from app.books.models import Book, Borrow


class InsufficientCopiesError(Exception):
    """Нет свободных экземпляров для выдачи."""


class BorrowNotFoundOrAlreadyClosedError(Exception):
    """Выдача не найдена или уже закрыта."""


class BookDAO(BaseDAO):
    model = Book


class BorrowDAO(BaseDAO):
    model = Borrow

    @classmethod
    async def create_borrow(cls, book_id: int, user_id: int) -> Borrow:
        """Атомарно создаёт запись о выдаче и уменьшает quantity_to_borrow.

        Защита от гонки: декремент идёт условием WHERE quantity_to_borrow > 0,
        поэтому при двух параллельных запросах только один изменит строку.
        """
        async with async_session_maker() as session:
            async with session.begin():
                dec = await session.execute(
                    update(Book)
                    .where(Book.id == book_id, Book.quantity_to_borrow > 0)
                    .values(quantity_to_borrow=Book.quantity_to_borrow - 1)
                )
                if dec.rowcount == 0:
                    raise InsufficientCopiesError(
                        f"Книга {book_id} недоступна для выдачи"
                    )

                borrow = Borrow(
                    book_id=book_id,
                    user_id=user_id,
                    issue_date=date.today(),
                )
                session.add(borrow)
                try:
                    await session.flush()
                except SQLAlchemyError as e:
                    await session.rollback()
                    raise e
                await session.refresh(borrow)
                return borrow

    @classmethod
    async def close_borrow(cls, instance_id: int) -> Borrow:
        """Атомарно закрывает выдачу и увеличивает quantity_to_borrow.

        Защита от двойного закрытия: WHERE return_date IS NULL +
        SELECT ... FOR UPDATE на выдачу.
        """
        async with async_session_maker() as session:
            async with session.begin():
                borrow = (
                    await session.execute(
                        select(cls.model)
                        .where(cls.model.id == instance_id)
                        .with_for_update()
                    )
                ).scalar_one_or_none()
                if borrow is None or borrow.return_date is not None:
                    raise BorrowNotFoundOrAlreadyClosedError(
                        f"Выдача {instance_id} не найдена или уже закрыта"
                    )

                borrow.return_date = date.today()
                await session.flush()

                inc = await session.execute(
                    update(Book)
                    .where(Book.id == borrow.book_id)
                    .values(quantity_to_borrow=Book.quantity_to_borrow + 1)
                )
                if inc.rowcount == 0:
                    raise SQLAlchemyError(
                        f"Не удалось инкрементировать остаток книги {borrow.book_id}"
                    )
                await session.refresh(borrow)
                return borrow
