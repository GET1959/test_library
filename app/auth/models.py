from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, int_pk, str_uniq


class User(Base):
    id: Mapped[int_pk]
    username: Mapped[str_uniq]
    email: Mapped[str_uniq] = mapped_column(String(length=320))
    hashed_password: Mapped[str] = mapped_column(String(length=1024))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f"<User {self.username}>"