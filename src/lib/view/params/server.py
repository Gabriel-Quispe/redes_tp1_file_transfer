from validations import (
    HostValidation,
    FolderValidation,
    PortValidation
)


class ServerParams:
    def __init__(self, params):
        self.host = params.host
        self.port = params.port
        self.storage = params.storage
        self.verbose = params.verbose
        self.quiet = params.quiet
        HostValidation.validate(self.host)
        PortValidation.validate(self.port)
        FolderValidation.validate(self.storage)
