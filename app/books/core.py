from sqlalchemy import update, event
from sqlalchemy.exc import SQLAlchemyError

from app.core.base import BaseDAO
from app.database import async_session_maker
from app.books.models import Book, Borrow


@event.listens_for(Borrow, 'after_insert')
def receive_after_insert(mapper, connection, target):
    book_id = target.book_id
    connection.execute(
        update(Book)
        .where(Book.id == book_id)
        .values(quantity_to_borrow=Book.quantity_to_borrow - 1)
    )


class BookDAO(BaseDAO):
    model = Book


class BorrowDAO(BaseDAO):
    model = Borrow

    @classmethod
    async def close_borrow(cls, instance_id, instance_data):
        async with async_session_maker() as session:
            async with session.begin():
                instance_dict = instance_data if isinstance(instance_data, dict) else instance_data.model_dump(
                    exclude_unset=True).items()
                query = (
                    update(cls.model)
                    .where(cls.model.id == instance_id)
                    .values(instance_dict)
                    .execution_options(synchronize_session="fetch")
                )
                result = await session.execute(query)

                update_book = (
                    update(Book)
                    .where(Book.id == cls.model.book_id)
                    .values(quantity_to_borrow=Book.quantity_to_borrow + 1)
                )
                await session.execute(update_book)

                try:
                    await session.commit()
                except SQLAlchemyError as e:
                    await session.rollback()
                    raise e
                return result.rowcount
