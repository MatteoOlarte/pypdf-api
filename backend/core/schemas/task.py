from typing import Optional
from datetime import datetime

from pydantic import BaseModel


from .filemodel import FileModelSchema

class TaskSchema(BaseModel):
    pk: int
    created: datetime
    updated: datetime
    status: 'StatusSchema'
    result: Optional['FileModelSchema'] = None


class StatusSchema(BaseModel):
    name: str