import hashlib

from sqlalchemy.orm import Session

from ..models import user as models
from ..schemas import user as schemas


def create_user(db: Session, *, user_in: schemas.UserCreate):
    sha256 = hashlib.sha256()
    sha256.update(user_in.password.encode('utf-8'))
    user_in.password = sha256.hexdigest()

    db_user = models.ModelUser(**user_in.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    db.rollback()
    return db_user


def get_by_email(db: Session, *, email: str):
    user_db = db.query(models.ModelUser).where(models.ModelUser.email == email).first()
    return user_db


def get_by_username(db: Session, *, username: str):
    user_db = db.query(models.ModelUser).where(models.ModelUser.first_name == username).first()
    return user_db


def get_by_id(db: Session, *, user_id: int):
    user_db = db.get(models.ModelUser, user_id)
    return user_db


def validate_password(password_a: str, password_b: str):
    """
    Validate password
    :param password_a: non-hashed password
    :param password_b: hashed password
    :return: True if the passwords match, False otherwise
    """
    sha256 = hashlib.sha256()
    sha256.update(password_a.encode('utf-8'))
    return sha256.hexdigest() == password_b
