<<<<<<< HEAD
from view.validations import FileValidation, HostValidation, PortValidation, ProtocolValidation


class UploadParams:
    def __init__(self, params) -> None:
        self.host     = params.host
        self.port     = params.port
        self.src      = params.src
        self.name     = params.name
        self.protocol = params.protocol
        self.verbose  = params.verbose
        self.quiet    = params.quiet
        HostValidation.validate(self.host)
        PortValidation.validate(self.port)
        FileValidation.validate(self.src)
=======
from validations import (
    HostValidation,
    FileValidation,
    PortValidation,
    NameValidation,
    ProtocolValidation,
)


class UploadParams:
    def __init__(self, params):
        self.host = params.host
        self.port = params.port
        self.src = params.src
        self.name = params.name
        self.protocol = params.protocol
        self.verbose = params.verbose
        self.quiet = params.quiet
        HostValidation.validate(self.host)
        PortValidation.validate(self.port)
        FileValidation.validate(self.src)
        NameValidation.validate(self.name)
>>>>>>> main
        ProtocolValidation.validate(self.protocol)
