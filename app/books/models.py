from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, int_pk, str_uniq, str_null_true, created_at


class Book(Base):
    id: Mapped[int_pk]
    title: Mapped[str_uniq]
    description: Mapped[str_null_true]
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"), nullable=False)
    quantity_to_borrow: Mapped[int]

    def __str__(self):
        return f"{self.title}"


class Borrow(Base):
    id: Mapped[int_pk]
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False)
    issue_date: Mapped[created_at]
    return_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    def __str__(self):
        return f"{self.__class__.__name__}(id={self.id}, issued {self.issue_date})"
