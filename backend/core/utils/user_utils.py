import hashlib

from sqlalchemy.orm import Session

from ..models import user as models
from ..schemas import user as schemas


def create_user(db: Session, *, user_in: schemas.UserCreate):
    sha256 = hashlib.sha256()
    sha256.update(user_in.password.encode('utf-8'))
    user_in.password = sha256.hexdigest()

    db_user = models.User(**user_in.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    # db.rollback()
    return db_user


def get_by_email(db: Session, *, email: str):
    user_db = db.query(models.User).where(models.User.email == email).first()
    return user_db


def get_by_username(db: Session, *, username: str):
    user_db = db.query(models.User).where(models.User.first_name == username).first()
    return user_db


def get_by_id(db: Session, *, user_id: int):
    user_db = db.get(models.User, user_id)
    return user_db
