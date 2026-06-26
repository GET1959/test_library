from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class AuthorSch(BaseModel):
    first_name: str = Field(..., min_length=1, description="Имя Автора")
    last_name: str = Field(..., min_length=1, description="Фамилия Автора")
    date_of_birth: date = Field(..., description="Дата рождения Автора")


class AuthorListSch(BaseModel):
    id: int = Field(..., description="ID Автора")
    first_name: str = Field(..., description="Имя Автора")
    last_name: str = Field(..., description="Фамилия Автора")
    date_of_birth: date = Field(..., description="Дата рождения Автора")


class AuthorUpdateSch(BaseModel):
    """Схема частичного обновления автора. Все поля опциональны."""
    first_name: Optional[str] = Field(None, min_length=1, description="Имя Автора")
    last_name: Optional[str] = Field(None, min_length=1, description="Фамилия Автора")
    date_of_birth: Optional[date] = Field(None, description="Дата рождения Автора")
