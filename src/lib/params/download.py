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
        HostValidation.validate(self.host)
        PortValidation.validate(self.port)
        FolderValidation.validate(self.dst)
        NameValidation.validate(self.name)
        ProtocolValidation.validate(self.protocol)
