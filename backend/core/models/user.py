import hashlib
from typing import Self, TYPE_CHECKING

from sqlalchemy import Boolean, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

from ..db import Base

if TYPE_CHECKING:
    from . import Task


class User(Base):
    __tablename__ = 'users'
    __table_args__ = (
        Index('idx_users_email', 'email', unique=True),
    )

    pk: Mapped[int] = mapped_column(Integer, name='user_id', primary_key=True)
    first_name: Mapped[str] = mapped_column(String(length=255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(length=255), nullable=False)
    email: Mapped[str] = mapped_column(String(length=255), nullable=False)
    password: Mapped[str] = mapped_column(String(length=255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    tasks: Mapped[list['Task']] = relationship(back_populates='user')

    def validate_password(self: Self, password: str) -> bool:
        sha256 = hashlib.sha256()
        sha256.update(password.encode('utf-8'))
        return self.password == sha256.hexdigest()

    def update(self: Self, db: Session) -> None:
        db.add(self)
        db.commit()
        db.refresh(self)

    def __eq__(self: Self, other) -> bool:
        return self.pk == other.pk
