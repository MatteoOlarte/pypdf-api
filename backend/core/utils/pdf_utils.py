from abc import ABC, abstractmethod
from typing import Self, override

from ..models import FileModel
from ..schemas.responses import ProcessResponse


class ProcessResponseBuilder(ABC):
    @abstractmethod
    def create(self: Self, task_status: str, task_name: str, timer: float = 0) -> ProcessResponse:
        pass


class FileProcessResponse(ProcessResponseBuilder):
    def __init__(self: Self, filemodel: FileModel) -> None:
        self.download_filename = filemodel.full_name
        self.download_path = filemodel.path
        self.output_filenumber = 1

    @override
    def create(self: Self, task_status: str, task_name: str, timer: float = 0) -> ProcessResponse:
        return ProcessResponse(
            download_filename=self.download_filename,
            download_path=self.download_path,
            output_filenumber=self.output_filenumber,
            timer=timer,
            task_status=task_status,
            task_name=task_name
        )
