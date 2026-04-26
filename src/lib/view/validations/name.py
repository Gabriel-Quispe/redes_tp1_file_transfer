import re


class NameValidation:
    @staticmethod
    def validate(name: str) -> None:
        if not name:
            raise ValueError("Filename cannot be empty")
        if re.search(r'[<>:"/\\|?*]', name):
            raise ValueError("Invalid characters in filename")
