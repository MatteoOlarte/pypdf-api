from fastapi import HTTPException
from fastapi import status


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