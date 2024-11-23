from abc import ABC, abstractmethod
from functools import reduce
from typing import Annotated, Optional, Self, override

from fastapi import File, HTTPException, status, UploadFile
from sqlalchemy.orm import Session

from ..errors import INVALID_FILE_ERROR
from ..models import ModelUser, UploadFileModel


class UploadFileModelFactory(ABC):
    def split_filename(self: Self, filename: str) -> tuple[str, str]:
        """
        Splits the given filename into the name and extension.

        :param filename: The full filename including the extension.
        :return: A tuple containing the name without the extension and the extension itself.
        """
        parts = filename.split('.')
        name = '.'.join(parts[0:-1])
        extension = f'.{parts[-1]}'
        return name, extension

    @abstractmethod
    def create_filemodel(self: Self, file: UploadFile, owner: Optional[ModelUser]) -> UploadFileModel:
        pass


class SimpleUploadFileFactory(UploadFileModelFactory):
    @override
    def create_filemodel(self: Self, file: UploadFile, owner: Optional[ModelUser]) -> UploadFileModel:
        fiename = file.filename

        if fiename:
            name, extension = self.split_filename(fiename)
            filemodel = UploadFileModel()
            filemodel.name = name
            filemodel.extension = extension
            filemodel.content_type = file.content_type or ''
            filemodel.owner = owner
            return filemodel

        raise INVALID_FILE_ERROR


def get_filemodel(
    db: Session,
    *,
    file_url: str,
) -> Optional[UploadFileModel]:
    filemodel = db.query(UploadFileModel).where(UploadFileModel.path == file_url).first()
    return filemodel


def check_size_or_raise(
        files: Annotated[list[UploadFile], File(...)],
        max_size: int = 1000
) -> None:
    file_size: float = reduce(lambda f1, f2: f1 + f2, [file.size for file in files if file.size])
    file_size /= 1_000_000

    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'file size is larger than {max_size:<1}mb limit',
            headers={
                'X-Error': 'FileTooLarge'
            }
        )
