import os


class FolderValidation:
    @staticmethod
    def validate(path):
        path = os.path.expanduser(path)
        if os.path.exists(path) and not os.path.isdir(path):
            raise ValueError("Path exists but is not a directory")
        parent = os.path.dirname(os.path.abspath(path))
        if not os.path.exists(parent):
            raise ValueError("Parent directory does not exist")
        if not os.access(parent, os.W_OK):
            raise ValueError("No write permission in parent directory")
