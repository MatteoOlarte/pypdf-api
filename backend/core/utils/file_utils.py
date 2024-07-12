from typing import Annotated
from functools import reduce

from fastapi import UploadFile, HTTPException, File, status


def check_size_or_raise(
        files: Annotated[list[UploadFile], File(...)],
        max_size: int = 1000
):
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
