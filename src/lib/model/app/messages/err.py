from __future__ import annotations

from model.codigos.cod_error import CodError
from model.codigos.cod_msj import CodMsj


class ErrMsg:
    """
    Formato: [TYPE(1)][CODE(1)]
    """

    def __init__(self, code: CodError) -> None:
        self.code = code

    # --- serialización ---
    def to_bytes(self) -> bytes:
        return bytes([CodMsj.ERR, self.code])

    @classmethod
    def from_bytes(cls, data: bytes) -> ErrMsg:
        return cls(code=CodError(data[1]))

    @staticmethod
    def peek_type(data: bytes) -> CodMsj:
        return CodMsj(data[0])
