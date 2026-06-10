from datetime import date
from fastapi import APIRouter, status, Depends, HTTPException

from app.authors.core import AuthorDAO
from app.books.core import (
    BookDAO,
    BorrowDAO,
    InsufficientCopiesError,
    BorrowNotFoundOrAlreadyClosedError,
)
from app.books.schemas import (
    BookSch,
    BookListSch,
    BookUpdateSch,
    BorrowSchCreate,
    BorrowListSch,
)
from app.auth.models import User
from app.auth.utils import get_current_active_user

router = APIRouter(prefix="/books")


@router.post(
    path="/",
    tags=["Книги"],
    status_code=status.HTTP_201_CREATED,
    summary="Добавление книги",
)
async def add_book(book: BookSch) -> dict:
    # Валидация автора на уровне роутера, чтобы не уезжать в БД с FK-ошибкой.
    author = await AuthorDAO.get_one_or_none_by_id(data_id=book.author_id)
    if author is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Автор с ID {book.author_id} не найден",
        )

    new_book = await BookDAO.add(**book.model_dump())
    if not new_book:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при добавлении книги",
        )
    return {"message": "Книга успешно добавлена", "id": new_book.id}


@router.get(
    path="/",
    tags=["Книги"],
    status_code=status.HTTP_200_OK,
    summary="Получение списка книг",
)
async def get_books() -> list[BookListSch]:
    return await BookDAO.get_all()


@router.get(
    path="/{book_id}/",
    tags=["Книги"],
    status_code=status.HTTP_200_OK,
    summary="Получение информации о книге по id",
)
async def get_book_by_id(book_id: int) -> BookListSch:
    result = await BookDAO.get_one_or_none_by_id(data_id=book_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID {book_id} не найдена",
        )
    return result


@router.patch(
    path="/{book_id}/",
    tags=["Книги"],
    status_code=status.HTTP_200_OK,
    summary="Частичное обновление информации о книге",
)
async def update_book(book_id: int, book_data: BookUpdateSch) -> BookListSch:
    existing = await BookDAO.get_one_or_none_by_id(data_id=book_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID {book_id} не найдена",
        )

    # Если клиент меняет автора — проверить, что он существует.
    if book_data.author_id is not None:
        author = await AuthorDAO.get_one_or_none_by_id(data_id=book_data.author_id)
        if author is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Автор с ID {book_data.author_id} не найден",
            )

    # model_dump(exclude_unset=True) — обновляем только то, что клиент реально прислал.
    values = book_data.model_dump(exclude_unset=True)
    if not values:
        # Нечего обновлять — отдаём текущее состояние без лишнего UPDATE.
        return existing

    result = await BookDAO.update_on_id(instance_id=book_id, instance_data=values)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID {book_id} не найдена",
        )
    return await BookDAO.get_one_or_none_by_id(data_id=book_id)


@router.delete(
    path="/{book_id}/",
    tags=["Книги"],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление книги",
)
async def delete_book(book_id: int) -> None:
    result = await BookDAO.delete(id=book_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID {book_id} не найдена",
        )
    # 204 No Content — тело ответа должно быть пустым.
    return None


@router.post(
    path="/borrows",
    tags=["Выдачи"],
    status_code=status.HTTP_201_CREATED,
    summary="Создание записи о выдаче книги",
)
async def add_borrow(
    borrow: BorrowSchCreate,
    current_user: User = Depends(get_current_active_user),
) -> BorrowListSch:
    try:
        return await BorrowDAO.create_borrow(
            book_id=borrow.book_id,
            user_id=current_user.id,
        )
    except InsufficientCopiesError:
        # Книга существует, но все экземпляры заняты — 409, а не 404.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Книга с ID {borrow.book_id} недоступна для выдачи",
        )


@router.get(
    path="/borrows",
    tags=["Выдачи"],
    status_code=status.HTTP_200_OK,
    summary="Получение списка всех выдач",
)
async def get_borrows() -> list[BorrowListSch]:
    return await BorrowDAO.get_all()


@router.get(
    path="/borrows/{borrow_id}/",
    tags=["Выдачи"],
    status_code=status.HTTP_200_OK,
    summary="Получение информации о выдаче по id",
)
async def get_borrow_by_id(borrow_id: int) -> BorrowListSch:
    result = await BorrowDAO.get_one_or_none_by_id(data_id=borrow_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Выдача с ID {borrow_id} не найдена",
        )
    return result


@router.patch(
    path="/borrows/{borrow_id}/return",
    tags=["Выдачи"],
    status_code=status.HTTP_200_OK,
    summary="Завершение выдачи",
)
async def close_borrow(borrow_id: int) -> BorrowListSch:
    try:
        return await BorrowDAO.close_borrow(instance_id=borrow_id)
    except BorrowNotFoundOrAlreadyClosedError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Выдача с ID {borrow_id} не найдена или уже закрыта",
        )


