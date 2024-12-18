from abc import ABC, abstractmethod
from functools import reduce
from typing import Annotated, Optional, Self, override

from fastapi import File, HTTPException, status, UploadFile
from sqlalchemy.orm import Session

from ..errors import INVALID_FILE_ERROR
from ..models import FileModel, Task


class FileModelFactory(ABC):
    @abstractmethod
    def create_filemodel(self: Self) -> FileModel:
        pass


class UploadFileModelFactory(FileModelFactory):
    def __init__(self: Self, upload_file: UploadFile, task: Task) -> None:
        super().__init__()
        self.upload_file = upload_file
        self.task = task

    @override
    def create_filemodel(self: Self) -> FileModel:
        filename = self.upload_file.filename
        content_type = self.upload_file.content_type

        if filename and content_type:
            filemodel = FileModel()
            name, extension = split_filename(filename)
            filemodel.name = name
            filemodel.extension = extension
            filemodel.content_type = content_type
            filemodel.task = self.task
            return filemodel
        raise INVALID_FILE_ERROR


class ResponseFileModelFactory(FileModelFactory):
    def __init__(self: Self, filename: str, content_type: str, task: Task) -> None:
        super().__init__()
        self.filename = filename
        self.content_type = content_type
        self.task = task

    @override
    def create_filemodel(self: Self) -> FileModel:
        filemodel = FileModel()
        name, extension = split_filename(self.filename)
        filemodel.name = name
        filemodel.extension = extension
        filemodel.content_type = self.content_type
        filemodel.task = self.task
        return filemodel


def get_filemodel(
        db: Session,
        *,
        file_url: str,
) -> Optional[FileModel]:
    filemodel = db.query(FileModel).where(FileModel.path == file_url).first()
    return filemodel


def split_filename(filename: str) -> tuple[str, str]:
    '''
    Splits the given filename into the name and extension.

    :param filename: The full filename including the extension.
    :return: A tuple containing the name without the extension and the extension itself.
    '''
    parts = filename.split('.')
    name = '.'.join(parts[0:-1])
    extension = f'.{parts[-1]}'
    return name, extension


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
