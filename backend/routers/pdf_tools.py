import io
import zipfile
from enum import Enum
from typing import Annotated

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

from ..dependencies import file_uploads, file_upload, get_file_or_raise, get_db, get_files
from ..core.utils import pair, pdf_utils
from ..core.models import FileModel
from ..core.schemas.responses import ProcessResponse
from ..core import errors
from sqlalchemy.orm import Session

from ..core.services.storage_service import LocalPdfWriterFile

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


@router.post('/merge')
async def merge_pdf(
        db: Annotated[Session, Depends(get_db)],
        filemodels: Annotated[list[FileModel], Depends(get_files)],
        strict: Annotated[bool, Query(..., description='strict mode')] = False
):
    '''
    Merge multiple PDF files into a single PDF file.
    - **strict**: If false then non-PDF files will be ignored. Otherwise, an error will be raised.
    - **upload_files**: Files to be merged.
    '''
    writer = pypdf.PdfWriter()
    merged_file = ...
    response_schema = ...

    if len(filemodels) < 2:
        raise errors.INSUFFICIENT_FILES_MERGE_ERROR
    
    for filemodel in filemodels:
        try:
            reader = pypdf.PdfReader(filemodel.absolute_path)
            writer.append(reader)
        except:
            if strict:
                raise errors.NOT_PDF_ERROR
            continue
    
    merge_pdf = LocalPdfWriterFile(writer, 'merged-pdf.pdf')
    await merge_pdf.upload('temp/results')
    


# @router.post('/merge')
# async def merge_pdf(
#     upload_files: Annotated[list[str], Depends(get_files_or_404)],
#     strict: Annotated[bool, Query(..., description='strict mode')] = False
# ) -> StreamingResponse:
#     """
#     Merge multiple PDF files into a single PDF file.
#     - **strict**: If false then non-PDF files will be ignored. Otherwise, an error will be raised.
#     - **upload_files**: Files to be merged.
#     """
#     ...
#     if len(upload_files) < 2:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail='at least 2 files are required for merging',
#             headers={
#                 'X-Error': 'InsufficientFiles'
#             }
#         )
#     writer = pypdf.PdfWriter()
#     headers = {}

#     for file in upload_files:
#         try:
#             await file.seek(0)
#             reader = pypdf.PdfReader(file.file)
#             writer.append(reader)
#         except PyPdfError:
#             if strict:
#                 raise non_pdf_error
#             continue
#     headers.update({
#         'Content-Type': 'application/pdf',
#         'Content-Disposition': f'attachment; filename=merged_pdf.pdf'
#     })
#     return StreamingResponse(
#         content=iter([__to_bytes(writer).getvalue()]),
#         media_type='application/pdf',
#         headers=headers
#     )


# @router.post('/lock', response_model=PDFProcessResponse)
# async def lock_pdf(
#         db: Annotated[Session, Depends(get_db)],
#         filemodel: Annotated[UploadFileModel, Depends(get_file_or_raise)],
#         password: Annotated[str, Query(..., description='password to unlock the PDF file')],
# ) -> PDFProcessResponse:
#     '''
#     Protect a PDF file with a password.
#     - **uploaded_files**: Files to be protected.
#     - **password**: Password to protect the PDF file.
#     '''
#     response_schema = pdf_utils.SinglePDFProcessResponse(filemodel)

#     try:
#         reader = pypdf.PdfReader(filemodel.absolute_path)
#         writer = pypdf.PdfWriter()
#         writer.append(reader)
#         writer.encrypt(password, None, True)
#         pdf_utils.write_bites(filemodel.absolute_path, writer)
#         filemodel.save(db)
#         return response_schema.create('TaskSuccess', 'PDFLock')
#     except:
#         db.rollback()
#         return response_schema.create('TaskFailed', 'PDFLock')


# @router.post('/unlock', response_model=PDFProcessResponse)
# async def unlock_pdf(
#         db: Annotated[Session, Depends(get_db)],
#         filemodel: Annotated[UploadFileModel, Depends(get_file_or_raise)],
#         password: Annotated[str, Query(..., description='password to unlock the PDF file')]
# ) -> PDFProcessResponse:
#     '''
#     Unlock a PDF file with a password.
#     - **upload_file**: File to be unlocked.
#     - **password**: Password to unlock the PDF file.
#     '''
#     response_schema = pdf_utils.SinglePDFProcessResponse(filemodel)

#     try:
#         reader = pypdf.PdfReader(filemodel.absolute_path)
#         writer = ...

#         if reader.is_encrypted:
#             reader.decrypt(password)
#             writer = pypdf.PdfWriter(clone_from=reader)
#             pdf_utils.write_bites(filemodel.absolute_path, writer)
#             filemodel.save(db)
#         return response_schema.create('TaskSuccess', 'PDFUnlock')
#     except PyPdfError:
#         db.rollback()
#         return response_schema.create('WrongPassword', 'PDFUnlock')
#     except Exception:
#         db.rollback()
#         return response_schema.create('TaskFailed', 'PDFUnlock')


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
