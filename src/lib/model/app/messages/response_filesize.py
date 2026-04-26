from __future__ import annotations
from model.codigos.cod_msj import CodMsj
from model.codigos.cod_state import CodState


class ResponseFilesizeMsg:
    """
    Formato: [TYPE(1)][STATE(1)][FILESIZE(4)]
    """
    def __init__(self, filesize: int) -> None:
        self.filesize = filesize

    def to_bytes(self) -> bytes:
        return (
            bytes([CodMsj.RESPONSE, CodState.OK])
            + self.filesize.to_bytes(4, byteorder="big")
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> ResponseFilesizeMsg:
        filesize = int.from_bytes(data[2:6], byteorder="big")
        return cls(filesize=filesize)
