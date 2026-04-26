from __future__ import annotations

from model.codigos.cod_msj import CodMsj
from model.codigos.cod_state import CodState


class ResponseOkMsg:
    """
    Formato: [TYPE(1)][STATE(1)]
    """

    def to_bytes(self) -> bytes:
        return bytes([CodMsj.RESPONSE, CodState.OK])

    @classmethod
    def from_bytes(cls, _data: bytes) -> ResponseOkMsg:
        return cls()
