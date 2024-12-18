import io
import zipfile
from enum import Enum
from typing import Annotated, Optional

import pypdf
from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    status,
    Depends,
    Query
)
from fastapi.responses import StreamingResponse
from pypdf.errors import PyPdfError

from ..dependencies import get_db, get_task, current_user_or_none
from ..core.utils import pair, pdf_utils
from ..core.models import FileModel, Task, User
from ..core.schemas import TaskSchema
from ..core import errors
from sqlalchemy.orm import Session

from ..core.services import storage_service as ss
from ..core.services import tasks_service as ts

router = APIRouter(prefix='/pdf-utilities', tags=['PDF Utilities'])


class SplitMode(str, Enum):
    PAGE_RANGES = 'ranges'
    PAGE_EXTRACT = 'extract'


# def __split_pdf(pdf_reader: pypdf.PdfReader, ranges: list[int]) -> dict[str, pypdf.PdfWriter]:
#     range_pairs = list(pair(ranges))
#     out: dict[str, pypdf.PdfWriter] = {}

#     for i, range_pair in enumerate(range_pairs):
#         writer = pypdf.PdfWriter()
#         start, end = range_pair
#         pages: list[pypdf.PageObject] = pdf_reader.pages[start-1:end]

#         for page in pages:
#             writer.add_page(page)
#         out.update({f'split_{i+1}.pdf': writer})

#     return out


# def __extract_pages(pdf_reader: pypdf.PdfReader, extract_pages: list[int]) -> pypdf.PdfWriter:
#     pdf_writer = pypdf.PdfWriter()

#     for i in extract_pages:
#         try:
#             page = pdf_reader.pages[i-1]
#             pdf_writer.add_page(page)
#         except IndexError:
#             continue

#     return pdf_writer


@router.post('/merge', response_model=TaskSchema)
async def merge_pdf(
        db: Annotated[Session, Depends(get_db)],
        task: Annotated[Task, Depends(get_task)],
        user: Annotated[User, Depends(current_user_or_none)],
        strict: Annotated[bool, Query(..., description='strict mode')] = False
) -> Task:
    '''
    Merge multiple PDF files into a single PDF file.
    - **strict**: If false then non-PDF files will be ignored. Otherwise, an error will be raised.
    - **upload_files**: Files to be merged.
    '''
    if not task.check_ownership(user):
        raise errors.FORBIDDEN_TASK
    
    try:
        task.result = await pdf_utils.merge_pdf(db, task, strict)
        ts.set_task_completed(db, task)
        task.update(db)
        return task
    except Exception as error:
        ts.set_task_failed(db, task)
        raise error
    

@router.post('/lock', response_model=TaskSchema)
async def lock_pdf(
        db: Annotated[Session, Depends(get_db)],
        task: Annotated[Task, Depends(get_task)],
        user: Annotated[User, Depends(current_user_or_none)],
        password: Annotated[str, Query(..., description='password to unlock the PDF file')]
) -> Task:
    '''
    Protect a PDF file with a password.
    - **uploaded_files**: Files to be protected.
    - **password**: Password to protect the PDF file.
    '''
    if not task.check_ownership(user):
        raise errors.FORBIDDEN_TASK
    
    try:
        task.result = await pdf_utils.lock_pdf(db, task, password)
        ts.set_task_completed(db, task)
        task.update(db)
        return task
    except Exception as error:
        ts.set_task_failed(db, task)
        raise error
    

@router.post('/unlock', response_model=TaskSchema)
async def unlock_pdf(
        db: Annotated[Session, Depends(get_db)],
        task: Annotated[Task, Depends(get_task)],
        user: Annotated[User, Depends(current_user_or_none)],
        password: Annotated[str, Query(..., description='password to unlock the PDF file')]
) -> Task:
    '''
    Unlock a PDF file with a password.
    - **upload_file**: File to be unlocked.
    - **password**: Password to unlock the PDF file.
    '''
    if not task.check_ownership(user):
        raise errors.FORBIDDEN_TASK
    
    try:
        task.result = await pdf_utils.unlock_pdf(db, task, password)
        ts.set_task_completed(db, task)
        task.update(db)
        return task
    except Exception as error:
        ts.set_task_failed(db, task)
        raise error


# @router.post('/split')
# async def split_pdf(
#         upload_file: Annotated[UploadFile, Depends(file_upload)],
#         split_mode: Annotated[SplitMode, SplitMode.PAGE_EXTRACT],
#         ranges: Annotated[list[int], Query()] = [],
#         extract_pages: Annotated[list[int], Query()] = [],
# ):
#     """
#     Split a PDF file into multiple files, or extract pages from a PDF file.
#     - **upload_file**: File to be split.
#     - **split_mode**: Mode to split the PDF file, either 'ranges' or 'extract'.
#     - **ranges**: Range of pages to split the PDF file, mandatory if split_mode is 'ranges'.
#     - **extract_pages**: Pages to extract from the PDF file, mandatory if split_mode is 'extract'.
#     """
#     reader = pypdf.PdfReader(upload_file.file)
#     buffer = None
#     writer = ...
#     headers = ...

#     if split_mode is SplitMode.PAGE_RANGES:
#         if not ranges:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail='ranges is required when using page_ranges mode',
#                 headers={'X-Error': 'RangesRequired'}
#             )
#         files = __split_pdf(reader, ranges)
#         buffer = __zip_files(files)
#         headers = {
#             'Content-Type': 'application/zip',
#             'Content-Disposition': f'attachment; filename=split_pdf.zip'
#         }

#     elif split_mode is SplitMode.PAGE_EXTRACT:
#         if not extract_pages:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail='extract_pages is required when using page_extract mode',
#                 headers={'X-Error': 'ExtractPagesRequired'}
#             )

#         writer = __extract_pages(reader, extract_pages)
#         buffer = __to_bytes(writer)
#         headers = {
#             'Content-Type': 'application/pdf',
#             'Content-Disposition': f'attachment; filename=extracted_pages.pdf'
#         }

#     if buffer:
#         return StreamingResponse(
#             content=iter([buffer.getvalue()]),
#             media_type='application/pdf',
#             headers=headers # type: ignore
#         )
#     raise HTTPException(
#         status_code=status.HTTP_400_BAD_REQUEST,
#         detail='invalid split mode',
#         headers={'X-Error': 'InvalidSplitMode'}
#     )

