from typing import Optional

import pypdf
import pypdf.errors
from sqlalchemy.orm import Session

from .. import errors
from ..models import FileModel, Task, User
from ..services.storage_service import LocalPdfWriterFile
from . import file_utils


async def merge_pdf(db: Session, task: Task, strict: bool) -> FileModel:
    filemodels = task.files
    writer = pypdf.PdfWriter()
    strategy = LocalPdfWriterFile(writer, 'merged-pdf.pdf')
    result = file_utils.ResponseFileModelFactory('merged-pdf.pdf', 'application/pdf', task).create_filemodel()

    if len(filemodels) < 2:
        raise errors.MERGE_ERROR

    for filemodel in filemodels:
        try:
            reader = pypdf.PdfReader(filemodel.absolute_path)
            writer.append(reader)
        except:
            if strict:
                raise errors.NOT_PDF_ERROR
            continue
    await result.upload(db, strategy, upload_to=_get_target_path(task.user))
    return result


async def lock_pdf(db: Session, task: Task, password: str) -> FileModel:
    filemodel = task.files[0]
    result = file_utils.ResponseFileModelFactory('locked-pdf.pdf', 'application/pdf', task).create_filemodel()
    strategy: LocalPdfWriterFile

    try:
        reader = pypdf.PdfReader(filemodel.absolute_path)
        writer = pypdf.PdfWriter()
        strategy = LocalPdfWriterFile(writer, 'locked-pdf.pdf')

        writer.append(reader)
        writer.encrypt(password, None, True)
        await result.upload(db, strategy, upload_to=_get_target_path(task.user))
        return result
    except:
        db.rollback()
        raise errors.LOCK_ERROR


async def unlock_pdf(db: Session, task: Task, password: str) -> FileModel:
    filemodel = task.files[0]
    result = file_utils.ResponseFileModelFactory('unlocked-pdf.pdf', 'application/pdf', task).create_filemodel()
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


def _get_target_path(user: Optional[User]) -> str:
    if user:
        return f'{user.email}/results'
    return 'temp/results'
