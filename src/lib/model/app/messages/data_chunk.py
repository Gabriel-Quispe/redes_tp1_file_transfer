from __future__ import annotations
from model.codigos.cod_msj import CodMsj

MAX_CHUNK_BYTES = 32768  # 32 KB


class DataChunkMsg:
    """
    Formato: [TYPE(1)][MORE(1)][PAYLOAD(N)]
    MORE=1 → hay más chunks; MORE=0 → último chunk.
    """
    def __init__(self, payload: bytes, more: bool) -> None:
        self.payload = payload
        self.more    = more

    def to_bytes(self) -> bytes:
        more_byte = b"\x01" if self.more else b"\x00"
        return bytes([CodMsj.DATA]) + more_byte + self.payload

    @classmethod
    def from_bytes(cls, data: bytes) -> DataChunkMsg:
        more    = data[1] == 1
        payload = data[2:]
        return cls(payload=payload, more=more)

    @classmethod
    def split_file(cls, file_data: bytes) -> list[DataChunkMsg]:
        """Divide file_data en DataChunkMsg listos para enviar."""
        size  = MAX_CHUNK_BYTES
        parts = [
            file_data[i: i + size]
            for i in range(0, max(len(file_data), 1), size)
        ]
        return [
            cls(payload=part, more=i < len(parts) - 1)
            for i, part in enumerate(parts)
        ]
