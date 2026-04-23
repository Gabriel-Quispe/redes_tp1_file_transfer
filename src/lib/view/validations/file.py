import os

class FileValidation:
    @staticmethod
    def validate(path):
        if not os.path.exists(path):
            raise ValueError("File does not exist")
        if not os.path.isfile(path):
            raise ValueError("Path is not a file")
        if not os.access(path, os.R_OK):
            raise ValueError("No read permission on file")
