from sqlalchemy import (Column, String, Integer, Boolean)

from ..db import Base


class ModelUser(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    first_name = Column(String(length=255))
    last_name = Column(String(length=255))
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
