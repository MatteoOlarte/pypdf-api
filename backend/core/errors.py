from fastapi import HTTPException
from fastapi import status


class HTTPError(Exception):
    """Base class for all HTTP errors."""

    def __init__(self, message: str, status_code: int = 500, *args: object) -> None:
        super().__init__(message, *args)
        self.message = message
        self.status_code = status_code

    def to_dict(self) -> dict:
        """Convert the error to a dictionary representation."""
        return {"error": self.message, "status_code": self.status_code}


EMAIL_IN_USE_ERROR = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail='Email is already registered',
    headers={
        'X-Error': 'EmailAlreadyRegistered'
    }
)

INVALID_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail='Invalid credentials. Could not validate user.',
    headers={
        'X-Error': 'InvalidCredentials'
    }
)

USER_NOT_FOUND_ERROR = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail='The user does not exist. Please try again.',
    headers={
        "WWW-Authenticate": "Bearer",
        'X-Error': 'UserNotFound'
    }
)

INACTIVE_USER_ERROR = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail='The user account is inactive. Please contact support.',
    headers={
        "X-Error": 'InactiveUser'
    }
)

FILE_NOT_FOUND_ERROR = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail='File not found',
    headers={
        'X-Error': 'FileNotFound'
    }
)

INVALID_FILE_ERROR = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid file upload: the file does not have a valid name. Please provide a valid file.",
    headers={
        "X-Error": "InvalidFileUpload"
    }
)

FILE_ACCESS_DENIED = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="You do not have permission to access this file.",
    headers={
        "X-Error": "ForbiddenFileAccess"
    }
)

MERGE_ERROR = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail='',
    headers={
        'X-Error': 'PdfMergeError'
    }
)

LOCK_ERROR = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail='',
    headers={
        'X-Error': 'PdfLockError'
    }
)

UNLOCK_ERROR = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail='',
    headers={
        'X-Error': 'PdfUnlockError'
    }
)

UNLOCK_ERROR_WP = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail='',
    headers={
        'X-Error': 'PdfUnlockErrorWrongPassword'
    }
)

NOT_PDF_ERROR = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail='file is not a PDF',
    headers={
        'X-Error': 'NonPDFFile'
    }
)

INVALID_TASK = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail='Task is invalid or not found',
    headers={
        'X-Error': 'InvalidTask'
    }
)

FORBIDDEN_TASK = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="You do not have permission to access this Task.",
    headers={"X-Error": "AccessDenied"}
)

# FILE_TOO_LARGE_EXCEPTION = HTTPException(
#     status_code=status.HTTP_400_BAD_REQUEST,
#     detail=f"File size is larger than {max_size} MB limit.",
#     headers={
#         "X-Error": "FileTooLarge"
#     }
# )
