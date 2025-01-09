from datetime import date

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, int_pk, str_uniq, str_null_true


class Author(Base):
    id: Mapped[int_pk]
    first_name: Mapped[str]
    last_name: Mapped[str]
    date_of_birth: Mapped[date]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
