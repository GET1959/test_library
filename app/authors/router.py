from fastapi import APIRouter, status, HTTPException

from app.authors.core import AuthorDAO
from app.authors.schemas import AuthorSch, AuthorListSch, AuthorUpdateSch

router = APIRouter(prefix="/authors", tags=["Авторы"])


@router.post(
    path="/",
    status_code=status.HTTP_201_CREATED,
    summary="Создание автора",
)
async def add_author(author: AuthorSch) -> dict:
    new_author = await AuthorDAO.add(**author.model_dump())
    if not new_author:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при добавлении автора",
        )
    return {"message": "Автор успешно добавлен", "id": new_author.id}


@router.get(
    path="/",
    status_code=status.HTTP_200_OK,
    summary="Получение списка авторов",
)
async def get_authors() -> list[AuthorListSch]:
    return await AuthorDAO.get_all()


@router.get(
    path="/{author_id}/",
    status_code=status.HTTP_200_OK,
    summary="Получение информации об авторе по id",
)
async def get_author_by_id(author_id: int) -> AuthorListSch:
    result = await AuthorDAO.get_one_or_none_by_id(data_id=author_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Автор с ID {author_id} не найден",
        )
    return result


@router.patch(
    path="/{author_id}/",
    status_code=status.HTTP_200_OK,
    summary="Частичное обновление информации об авторе",
)
async def update_author(author_id: int, author_data: AuthorUpdateSch) -> AuthorListSch:
    existing = await AuthorDAO.get_one_or_none_by_id(data_id=author_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Автор с ID {author_id} не найден",
        )

    values = author_data.model_dump(exclude_unset=True)
    if not values:
        return existing

    result = await AuthorDAO.update_on_id(instance_id=author_id, instance_data=values)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Автор с ID {author_id} не найден",
        )
    return await AuthorDAO.get_one_or_none_by_id(data_id=author_id)


@router.delete(
    path="/{author_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление автора",
)
async def delete_author(author_id: int) -> None:
    result = await AuthorDAO.delete(id=author_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Автор с ID {author_id} не найден",
        )
    return None
