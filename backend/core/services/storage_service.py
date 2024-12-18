import os
from abc import ABC, abstractmethod
from typing import Self, override
from uuid import uuid4

from fastapi import UploadFile
from pypdf import PdfWriter

from ...config import BASE_DIR, UPLOAD_DIR


class StorageStrategy(ABC):
    '''
    Abstract base class for defining a storage strategy.

    Concrete implementations must provide methods for uploading and deleting files.
    '''

    @abstractmethod
    async def upload(self: Self, upload_to: str) -> str:
        '''
        Uploads a file to the specified destination.

        Args:
            target_path (str): The target path or location where the file will be stored.

        Returns:
            str: A string representing the path or URL where the file has been uploaded.
        '''
        pass

    @abstractmethod
    async def delete(self: Self, file_path: str) -> bool:
        '''
        Deletes a file from the specified path.

        Args:
            file_path (str): The path of the file to be deleted.

        Returns:
            bool: True if the file was successfully deleted, False otherwise.
        '''


class LocalUploadFile(StorageStrategy):
    def __init__(self: Self, upload_file: UploadFile) -> None:
        super().__init__()
        self.upload_file = upload_file

    @override
    async def upload(self: Self, upload_to: str) -> str:
        dir_path: str = _make_dirs(os.path.join(UPLOAD_DIR, upload_to))
        filename: str = _get_hashes_file_name(self.upload_file.filename)  # type: ignore
        filepath: str = os.path.join(dir_path, filename)

        with open(filepath, "wb") as buffer:
            buffer.write(await self.upload_file.read())
        return filepath.replace('\\', '/')

    @override
    async def delete(self: Self, file_path: str) -> bool:
        return _delete_file(file_path)


class LocalExistingFile(StorageStrategy):
    def __init__(self: Self, filepath: str) -> None:
        super().__init__()
        self.filepath = filepath

    @override
    async def upload(self: Self, upload_to: str) -> str:
        return self.filepath

    @override
    async def delete(self: Self, file_path: str) -> bool:
        return _delete_file(file_path)


class LocalPdfWriterFile(StorageStrategy):
    def __init__(self: Self, writer: PdfWriter, filename: str) -> None:
        super().__init__()
        self.writer = writer
        self.filename = filename

    @override
    async def upload(self: Self, upload_to: str) -> str:
        print(UPLOAD_DIR)
        dir_path: str = _make_dirs(os.path.join(UPLOAD_DIR, upload_to))
        filepath: str = os.path.join(dir_path, _get_hashes_file_name(self.filename))

        with open(filepath, 'wb') as file:
            self.writer.write(file)
        return filepath.replace('\\', '/')

    @override
    async def delete(self: Self, file_path: str) -> bool:
        return _delete_file(file_path)


def _delete_file(file_path: str):
    full_path = os.path.join(BASE_DIR, file_path)

    if os.path.exists(full_path):
        os.remove(full_path)
        return True
    return False


def _get_hashes_file_name(filename: str) -> str:
    unique_id = uuid4().hex[:16]
    return f'file_{unique_id}_{filename}'


def _make_dirs(dir_path: str) -> str:
    os.makedirs(dir_path, exist_ok=True)
    return dir_path
