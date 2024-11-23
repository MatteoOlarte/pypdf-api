import hashlib
from typing import Self

from sqlalchemy import Boolean, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


class ModelUser(Base):
    __tablename__ = 'users'
    __table_args__ = (
        Index('idx_users_email', 'email', unique=True),
    )

    pk: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(length=255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(length=255), nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    uploaded_files = relationship('UploadFileModel')
    
    def validate_password(self: Self, password: str) -> bool:
        sha256 = hashlib.sha256()
        sha256.update(password.encode('utf-8'))
        return self.password == sha256.hexdigest()
