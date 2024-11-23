from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FileModelBase(BaseModel):
    path: str
    content_type: str
    created: datetime
    updated: datetime
    owner_id: Optional[int]


class FileModelCreate(FileModelBase):
    pass


class FileModelSchema(FileModelBase):
    full_name: str
    is_uploaded: bool
    # absolute_path: Optional[str]

    model_config = {
        'from_attributes': True
    }
