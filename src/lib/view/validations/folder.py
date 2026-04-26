import os
from pathlib import Path


class FolderValidation:
    @staticmethod
    def validate(path: str) -> None:
        p = Path(path).expanduser()

        if p.exists() and not p.is_dir():
            raise ValueError("Path exists but is not a directory")

        parent = p.resolve().parent

        if not parent.exists():
            raise ValueError("Parent directory does not exist")
        if not os.access(parent, os.W_OK):
            raise ValueError("No write permission in parent directory")
