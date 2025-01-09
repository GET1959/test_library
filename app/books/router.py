from datetime import date
from fastapi import APIRouter, status

from app.authors.core import AuthorDAO
from app.books.core import BookDAO, BorrowDAO
from app.books.schemas import BookSch, BookListSch, BorrowSch, BorrowSchCreate, BorrowListSch

router = APIRouter(prefix="/books")


@router.post(
    path="/books",
    tags=["Книги"],
    status_code=status.HTTP_200_OK,
    summary="Добавление книги",
)
async def add_book(book: BookSch) -> dict:
    author_list = await AuthorDAO.get_all()
    author_id_list = [author.id for author in author_list]
    if book.author_id in author_id_list:
        check = await BookDAO.add(**book.dict())
        if check:
            return {"message": "Книга успешно добавлена"}
        else:
            return {"message": "Ошибка при добавлении книги"}

    else:
        return {"message": "Автора книги нет в списке"}


@router.get(
    path="/books/",
    tags=["Книги"],
    status_code=status.HTTP_200_OK,
    summary="Получение списка книг",
)
async def get_books() -> list[BookListSch]:
    return await BookDAO.get_all()


@router.get(
    path="/books/{id}/",
    tags=["Книги"],
    status_code=status.HTTP_200_OK,
    summary="Получение информации о книге по id",
)
async def get_book_by_id(book_id: int) -> BookSch | dict:
    result = await BookDAO.get_one_or_none_by_id(data_id=book_id)
    if result is None:
        return {'message': f'Книга с ID {book_id} не найдена!'}
    return result


@router.put(
    path="/authors/{id}/",
    tags=["Книги"],
    status_code=status.HTTP_200_OK,
    summary="Обновление информации о книге",
)
async def update_book(
        book_id: int,
        book_data: BookSch

):
    result = await BookDAO.update_on_id(instance_id=book_id,
                                        instance_data=book_data)
    if not result:
        return {'message': f'Книга с ID {book_id} не найдена!'}
    return book_data


@router.delete(
    path="/delete/{book_id}",
    tags=["Книги"],
    status_code=status.HTTP_200_OK,
    summary="Удаление книги",
)
async def delete_book(book_id: int) -> dict:
    check = await BookDAO.delete(id=book_id)
    if check:
        return {"message": f"Книга с ID {book_id} удалена!"}
    else:
        return {"message": "Ошибка при удалении книги!"}


@router.post(
    path="/borrows",
    tags=["Выдачи"],
    status_code=status.HTTP_200_OK,
    summary="Создание записи о выдаче книги",
)
async def add_borrow(borrow: BorrowSchCreate) -> dict:
    book_list = await BookDAO.get_all()
    book_id_list = [book.id for book in book_list if book.quantity_to_borrow > 0]
    if borrow.book_id in book_id_list:
        result = await BorrowDAO.add(**borrow.dict())
        if result:
            return {"message": "Выдача добавлена в список"}
        else:
            return {"message": "Ошибка при регистрации выдачи"}

    else:
        return {"message": "Этой книги нет в библиотеке"}


@router.get(
    path="/borrows",
    tags=["Выдачи"],
    status_code=status.HTTP_200_OK,
    summary="Получение списка всех выдач",
)
async def get_borrows() -> list[BorrowListSch]:
    return await BorrowDAO.get_all()


@router.get(
    path="/borrows/{id}/",
    tags=["Выдачи"],
    status_code=status.HTTP_200_OK,
    summary="Получение информации о выдаче по id",
)
async def get_borrow_by_id(borrow_id: int) -> BorrowSch | dict:
    result = await BorrowDAO.get_one_or_none_by_id(data_id=borrow_id)
    if not result:
        return {'message': f'Выдача с ID {borrow_id} не найдена!'}
    return result


@router.patch(
    path="/borrows/{id}/return",
    tags=["Выдачи"],
    status_code=status.HTTP_200_OK,
    summary="Завершение выдачи",
)
async def close_borrow(
        borrow_id: int,
) -> BorrowListSch | dict:
    result = await BorrowDAO.close_borrow(instance_id=borrow_id,
                                          instance_data={"return_date": date.today()})
    if result:
        return await BorrowDAO.get_one_or_none_by_id(data_id=borrow_id)
    else:
        return {'message': f'Книга с ID {borrow_id} не найдена!'}
