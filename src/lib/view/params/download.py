<<<<<<< HEAD
from view.validations import FolderValidation, HostValidation, NameValidation, PortValidation, ProtocolValidation
from pathlib import Path


class DownloadParams:
    def __init__(self, params) -> None:
        self.host     = params.host
        self.port     = params.port
        self.dst      = params.dst
        self.name     = params.name
        self.protocol = params.protocol
        self.verbose  = params.verbose
        self.quiet    = params.quiet
=======
from validations import (
    HostValidation,
    FolderValidation,
    NameValidation,
    PortValidation,
    ProtocolValidation
)


class DownloadParams:
    def __init__(self, params):
        self.host = params.host
        self.port = params.port
        self.dst = params.dst
        self.name = params.name
        self.protocol = params.protocol
        self.verbose = params.verbose
        self.quiet = params.quiet
>>>>>>> main
        HostValidation.validate(self.host)
        PortValidation.validate(self.port)
        FolderValidation.validate(self.dst)
        NameValidation.validate(self.name)
        ProtocolValidation.validate(self.protocol)
<<<<<<< HEAD

    @property
    def addr(self) -> tuple[str, int]:
        return (self.host, self.port)

    @property
    def dest_path(self) -> Path:
        return Path(self.dst) / self.name
=======
>>>>>>> main
