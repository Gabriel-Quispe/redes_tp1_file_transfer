import os
from pathlib import Path


class FileValidation:
    @staticmethod
    def validate(path: str) -> None:
        p = Path(path)

        if not p.exists():
            raise ValueError("File does not exist")
        if not p.is_file():
            raise ValueError("Path is not a file")
        if not os.access(p, os.R_OK):
            raise ValueError("No read permission on file")
