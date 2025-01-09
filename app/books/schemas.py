from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class BookSch(BaseModel):
    title: str = Field(..., description="Название книги")
    description: str = Field(..., description="Краткое содержание книги")
    author_id: int = Field(..., description="ID Автора книги")
    quantity_to_borrow: int = Field(..., description="Количество доступных экземпляров")


class BookListSch(BaseModel):
    id: int = Field(..., description="ID книги")
    title: str = Field(..., description="Название книги")
    description: str = Field(..., description="Краткое содержание книги")
    author_id: int = Field(..., description="ID Автора книги")
    quantity_to_borrow: int = Field(..., description="Количество доступных экземпляров")


class BorrowSchCreate(BaseModel):
    book_id: int = Field(..., description="ID книги")
    issue_date: date = Field(..., description="Дата выдачи")


class BorrowSch(BaseModel):
    book_id: int = Field(..., description="ID книги")
    issue_date: date = Field(..., description="Дата выдачи")
    return_date: Optional[date] = Field(..., description="Дата возврата")


class BorrowListSch(BaseModel):
    id: int = Field(..., description="ID выдачи")
    book_id: int = Field(..., description="ID книги")
    issue_date: date = Field(..., description="Дата выдачи")
    return_date: Optional[date] = Field(..., description="Дата возврата")
