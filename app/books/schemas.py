from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class BookSch(BaseModel):
    title: str = Field(..., min_length=1, description="Название книги")
    description: Optional[str] = Field(None, description="Краткое содержание книги")
    author_id: int = Field(..., description="ID Автора книги")
    quantity_to_borrow: int = Field(..., ge=0, description="Количество доступных экземпляров")


class BookListSch(BaseModel):
    id: int = Field(..., description="ID книги")
    title: str = Field(..., description="Название книги")
    description: Optional[str] = Field(None, description="Краткое содержание книги")
    author_id: int = Field(..., description="ID Автора книги")
    quantity_to_borrow: int = Field(..., description="Количество доступных экземпляров")


class BookUpdateSch(BaseModel):
    """Схема частичного обновления книги. Все поля опциональны."""
    title: Optional[str] = Field(None, description="Название книги")
    description: Optional[str] = Field(None, description="Краткое содержание книги")
    author_id: Optional[int] = Field(None, description="ID Автора книги")
    quantity_to_borrow: Optional[int] = Field(
        None, description="Количество доступных экземпляров", ge=0
    )


class BorrowSchCreate(BaseModel):
    book_id: int = Field(..., description="ID книги")


class BorrowListSch(BaseModel):
    id: int = Field(..., description="ID выдачи")
    book_id: int = Field(..., description="ID книги")
    user_id: int = Field(..., description="ID пользователя")
    issue_date: date = Field(..., description="Дата выдачи")
    return_date: Optional[date] = Field(None, description="Дата возврата")

