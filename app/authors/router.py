from fastapi import APIRouter, Request, status

from app.authors.core import AuthorDAO
from app.authors.schemas import AuthorSch, AuthorListSch

router = APIRouter(prefix="/authors", tags=["Авторы"])


@router.post(
    path="/authors",
    status_code=status.HTTP_200_OK,
    summary="Создание автора",
)
async def add_author(author: AuthorSch) -> dict:
    check = await AuthorDAO.add(**author.dict())
    if check:
        return {"message": "Автор успешно добавлен"}
    else:
        return {"message": "Ошибка при добавлении автора"}


@router.get(
    path="/authors/",
    status_code=status.HTTP_200_OK,
    summary="Получение списка авторов",
)
async def get_authors() -> list[AuthorListSch]:
    return await AuthorDAO.get_all()


@router.get(
    path="/authors/{id}/",
    status_code=status.HTTP_200_OK,
    summary="Получение информации об авторе по id",
)
async def get_author_by_id(author_id: int) -> AuthorSch | dict:
    try:
        result = await AuthorDAO.get_one_or_none_by_id(data_id=author_id)
        return result
    except:
        return {'message': f'Автор с ID {author_id} не найден!'}


@router.put(
    path="/authors/{id}/",
    status_code=status.HTTP_200_OK,
    summary="Обновление информации об авторе",
)
async def update_author(
        author_id: int,
        author_data: AuthorSch

):
    result = await AuthorDAO.update_on_id(instance_id=author_id,
                                          instance_data=author_data)
    if not result:
        return {'message': f'Автор с ID {author_id} не найден!'}
    return author_data


@router.delete(
    path="/delete/{author_id}",
    status_code=status.HTTP_200_OK,
    summary="Удаление автора",
)
async def delete_author(author_id: int) -> dict:
    check = await AuthorDAO.delete(id=author_id)
    if check:
        return {"message": f"Автор с ID {author_id} удален!"}
    else:
        return {"message": "Ошибка при удалении автора!"}
