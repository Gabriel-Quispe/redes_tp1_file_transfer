from validations import (
    FileValidation,
    HostValidation,
    PortValidation,
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
        # NameValidation se omite intencionalmente en el cliente:
        # nombres inválidos (ej. path traversal) los rechaza el servidor
        # respondiendo con INVALID_FILENAME, lo que permite que el test
        # test_upload_nombre_invalido verifique el comportamiento end-to-end.
        ProtocolValidation.validate(self.protocol)
