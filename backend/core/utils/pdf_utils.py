from typing import Optional, Self, override
from enum import Enum
import io
import zipfile
from abc import ABC, abstractmethod

import pypdf
import pypdf.errors
from sqlalchemy.orm import Session

from . import pair
from .. import errors
from ..models import FileModel, Task, User
from ..services.storage_service import LocalPdfWriterFile, LocalPDFZipFile
from . import file_utils


class SplitMode(str, Enum):
    RANGE = 'range_split'
    PAGE = 'page_split'
    SIZE = 'size_split'


class PdfProcessStrategy(ABC):
    @abstractmethod
    def start_process(self: Self, reader: pypdf.PdfReader) -> None:
        pass

    @abstractmethod
    async def get_filemodel(self: Self, db: Session, user: Optional[User]) -> FileModel:
        pass


class PdfSlicerM(PdfProcessStrategy):
    def __init__(self: Self, ranges: list[int]) -> None:
        super().__init__()
        self.ranges: list[tuple[int, int]] = list(pair(ranges))
        self.pages: list[pypdf.PageObject] = []

    @override
    def start_process(self: Self, reader: pypdf.PdfReader) -> None:
        for r in self.ranges:
            start, end = r

            for page in reader.pages[start-1:end]:
                self.pages.append(page)

    @override
    async def get_filemodel(self: Self, db: Session, user: Optional[User]) -> FileModel:
        filemodel = file_utils.ResponseFileModelFactory('split-pdf.pdf', 'application/pdf').create_filemodel()
        writer = self.__merge_pages()
        strategy = LocalPdfWriterFile(writer, 'split-pdf.pdf')
        await filemodel.upload(db, strategy, upload_to=_get_target_path(user))
        return filemodel

    def __merge_pages(self: Self) -> pypdf.PdfWriter:
        writer = pypdf.PdfWriter()

        for page in self.pages:
            writer.add_page(page)
        return writer


class PdfSlicerZ(PdfProcessStrategy):
    def __init__(self: Self, ranges: list[int]) -> None:
        super().__init__()
        self.ranges:  list[tuple[int, int]] = list(pair(ranges))
        self.writers: list[tuple[str, pypdf.PdfWriter]] = []

    @override
    def start_process(self: Self, reader: pypdf.PdfReader) -> None:
        for index, r in enumerate(self.ranges):
            start, end = r
            writer = pypdf.PdfWriter()

            for page in reader.pages[start-1:end]:
                writer.add_page(page)
            self.writers.append((f'range-[{index+1}].pdf', writer))

    @override
    async def get_filemodel(self: Self, db: Session, user: Optional[User]) -> FileModel:
        strategy = LocalPDFZipFile(self.writers, 'split-pdf.zip')
        filemodel = file_utils.ResponseFileModelFactory('split-pdf.zip', 'application/zip').create_filemodel()
        await filemodel.upload(db, strategy, upload_to=_get_target_path(user))
        return filemodel
    

class PagesExtractM(PdfProcessStrategy):
    def __init__(self: Self, pages: list[int]) -> None:
        super().__init__()
        self.pages = pages
        self.writer = pypdf.PdfWriter()

    @override
    def start_process(self: Self, reader: pypdf.PdfReader) -> None:
        for index in self.pages:
            try:
                page = reader.pages[index-1]
                self.writer.add_page(page)
            except IndexError:
                continue

    @override
    async def get_filemodel(self: Self, db: Session, user: Optional[User]) -> FileModel:
        filemodel = file_utils.ResponseFileModelFactory('extracted pages-pdf.pdf', 'application/pdf').create_filemodel()
        strategy = LocalPdfWriterFile(self.writer, 'extracted pages-pdf.pdf')
        await filemodel.upload(db, strategy, upload_to=_get_target_path(user))
        return filemodel


class PagesExtractZ(PdfProcessStrategy):
    def __init__(self: Self, pages: list[int]) -> None:
        super().__init__()
        self.pages = pages
        self.writers: list[tuple[str, pypdf.PdfWriter]] = []

    @override
    def start_process(self: Self, reader: pypdf.PdfReader) -> None:
        for index, page_number in enumerate(self.pages):
            try:
                writer = pypdf.PdfWriter()
                page = reader.pages[page_number-1]
                writer.add_page(page)
                self.writers.append((f'page-[{index+1}].pdf', writer))
            except IndexError:
                continue

    @override
    async def get_filemodel(self: Self, db: Session, user: Optional[User]) -> FileModel:
        strategy = LocalPDFZipFile(self.writers, 'extracted pages.zip')
        filemodel = file_utils.ResponseFileModelFactory('extracted pages.zip', 'application/zip').create_filemodel()
        await filemodel.upload(db, strategy, upload_to=_get_target_path(user))
        return filemodel


async def merge_pdf(db: Session, /, task: Task, strict: bool) -> FileModel:
    filemodels = task.files
    writer = pypdf.PdfWriter()
    strategy = LocalPdfWriterFile(writer, 'merged-pdf.pdf')
    result = file_utils.ResponseFileModelFactory('merged-pdf.pdf', 'application/pdf').create_filemodel()

    if len(filemodels) < 2:
        raise errors.MERGE_ERROR

    for filemodel in filemodels:
        try:
            reader = pypdf.PdfReader(filemodel.absolute_path)
            writer.append(reader)
            reader.close()
        except:
            if strict:
                raise errors.NOT_PDF_ERROR
            continue
    await result.upload(db, strategy, upload_to=_get_target_path(task.user))
    return result


async def lock_pdf(db: Session, /, task: Task, password: str) -> FileModel:
    if len(task.files) == 0:
        raise errors.LOCK_ERROR
    filemodel = task.files[0]
    result = file_utils.ResponseFileModelFactory('locked-pdf.pdf', 'application/pdf').create_filemodel()
    strategy: LocalPdfWriterFile

    try:
        reader = pypdf.PdfReader(filemodel.absolute_path)
        writer = pypdf.PdfWriter()
        strategy = LocalPdfWriterFile(writer, 'locked-pdf.pdf')

        writer.append(reader)
        writer.encrypt(password, None, True)
        await result.upload(db, strategy, upload_to=_get_target_path(task.user))
        reader.close()
        return result
    except:
        db.rollback()
        raise errors.LOCK_ERROR


async def unlock_pdf(db: Session, /, task: Task, password: str) -> FileModel:
    if len(task.files) == 0:
        raise errors.UNLOCK_ERROR
    filemodel = task.files[0]
    result = file_utils.ResponseFileModelFactory('unlocked-pdf.pdf', 'application/pdf').create_filemodel()
    strategy: LocalPdfWriterFile

    try:
        reader = pypdf.PdfReader(filemodel.absolute_path)
        writer = ...

        if reader.is_encrypted:
            reader.decrypt(password)
            writer = pypdf.PdfWriter(clone_from=reader)
            strategy = LocalPdfWriterFile(writer, 'unlocked-pdf.pdf')
            await result.upload(db, strategy, upload_to=_get_target_path(task.user))
        return result
    except pypdf.errors.PyPdfError:
        db.rollback()
        raise errors.UNLOCK_ERROR_WP
    except Exception:
        db.rollback()
        raise errors.UNLOCK_ERROR


async def rangesplit_pdf(db: Session, /, task: Task, ranges: list[int], merge: bool) -> FileModel:
    if len(task.files) == 0:
        raise errors.SPLIT_ERROR
    filemodel = task.files[0]

    try:
        pdfreader = pypdf.PdfReader(filemodel.path)
        pdfslicer = PdfSlicerM(ranges) if merge else PdfSlicerZ(ranges)
        pdfslicer.start_process(pdfreader)
        return await pdfslicer.get_filemodel(db, task.user)
    except Exception:
        db.rollback()
        raise errors.SPLIT_ERROR


async def pagesplit_pdf(db: Session, /, task: Task, pages: list[int], merge: bool) -> FileModel:
    if len(task.files) == 0:
        raise errors.SPLIT_ERROR
    filemodel = task.files[0]

    try:
        pdfreader = pypdf.PdfReader(filemodel.path)
        pdfslicer = PagesExtractM(pages) if merge else PagesExtractZ(pages)
        pdfslicer.start_process(pdfreader)
        return await pdfslicer.get_filemodel(db, task.user)
    except Exception:
        db.rollback()
        raise errors.SPLIT_ERROR


def _get_target_path(user: Optional[User]) -> str:
    if user:
        return f'{user.email}/results'
    return 'temp/results'