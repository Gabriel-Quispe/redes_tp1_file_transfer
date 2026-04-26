from __future__ import annotations
from model.codigos.cod_msj import CodMsj
from model.codigos.cod_op import CodOp
from model.codigos.cod_protocol import CodProtocol

MAX_FILENAME_LENGTH = 255


class RequestUploadMsg:
    """
    Formato: [TYPE(1)][OP(1)][PROTOCOL(1)][FILESIZE(4)][FILENAME_LEN(1)][FILENAME(N)]
    """
    def __init__(self, protocol: CodProtocol, filename: str, filesize: int) -> None:
        self.protocol = protocol
        self.filename = filename
        self.filesize = filesize

    def to_bytes(self) -> bytes:
        encoded = self._encode_filename(self.filename)
        return (
            bytes([CodMsj.REQUEST, CodOp.UPLOAD, self.protocol])
            + self.filesize.to_bytes(4, byteorder="big")
            + encoded
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> RequestUploadMsg:
        protocol = CodProtocol(data[2])
        filesize = int.from_bytes(data[3:7], byteorder="big")
        filename = cls._decode_filename(data, offset=7)
        return cls(protocol=protocol, filename=filename, filesize=filesize)

    @staticmethod
    def _encode_filename(filename: str) -> bytes:
        encoded = filename.encode("utf-8")
        if len(encoded) > MAX_FILENAME_LENGTH:
            raise ValueError(f"Nombre de archivo demasiado largo: {len(encoded)} bytes")
        return bytes([len(encoded)]) + encoded

    @staticmethod
    def _decode_filename(data: bytes, offset: int) -> str:
        length = data[offset]
        return data[offset + 1: offset + 1 + length].decode("utf-8")
