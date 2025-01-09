from datetime import date

from pydantic import BaseModel, Field


class AuthorSch(BaseModel):
    first_name: str = Field(..., description="Имя Автора")
    last_name: str = Field(..., description="Фамилия Автора")
    date_of_birth: date = Field(..., description="Дата рождения Автора")


class AuthorListSch(BaseModel):
    id: int = Field(..., description="ID Автора")
    first_name: str = Field(..., description="Имя Автора")
    last_name: str = Field(..., description="Фамилия Автора")
    date_of_birth: date = Field(..., description="Дата рождения Автора")
