import struct

from app.codigos.cod_error import CodError
from app.codigos.cod_msj import CodMsj
from app.codigos.cod_op import CodOp
from app.codigos.cod_state import CodState


class MessageSerializer:
    """
    Construye y parsea los mensajes binarios del protocolo de aplicación.
    No conoce sockets, no orquesta flujos.

    Fragmentación de DATA:
      Los archivos se envían en chunks de MAX_CHUNK_BYTES.
      Cada chunk es un mensaje DATA independiente:
        [TYPE=DATA(1)][MORE(1)][chunk_bytes]
      MORE=1 → hay más chunks; MORE=0 → último chunk.
    """

    MAX_FILENAME_LENGTH = 255
    MAX_CHUNK_BYTES = 32768   # 32 KB por chunk — bien por debajo del límite UDP

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------

    def build_request_upload(self, filename: str, filesize: int) -> bytes:
        return (
            bytes([CodMsj.REQUEST, CodOp.UPLOAD])
            + filesize.to_bytes(4, byteorder="big")
            + self._encode_filename(filename)
        )

    def build_request_download(self, filename: str) -> bytes:
        return bytes([CodMsj.REQUEST, CodOp.DOWNLOAD]) + self._encode_filename(filename)

    def build_response_ok(self) -> bytes:
        return bytes([CodMsj.RESPONSE, CodState.OK])

    def build_response_ok_filesize(self, filesize: int) -> bytes:
        return bytes([CodMsj.RESPONSE, CodState.OK]) + filesize.to_bytes(4, byteorder="big")

    def build_data_chunk(self, chunk: bytes, more: bool) -> bytes:
        """Un chunk de datos con flag MORE."""
        more_byte = b"\x01" if more else b"\x00"
        return bytes([CodMsj.DATA]) + more_byte + chunk

    def build_err(self, code: CodError) -> bytes:
        return bytes([CodMsj.ERR, code])

    # Compatibilidad con código existente que llama build_data(file_data)
    def build_data(self, file_data: bytes) -> bytes:
        """Construye un único mensaje DATA (sin fragmentar). Solo para payloads pequeños."""
        return self.build_data_chunk(file_data, more=False)

    # ------------------------------------------------------------------
    # Parsers
    # ------------------------------------------------------------------

    def parse_type(self, data: bytes) -> CodMsj:
        return CodMsj(data[0])

    def parse_request_upload(self, data: bytes) -> tuple[str, int]:
        filesize = int.from_bytes(data[2:6], byteorder="big")
        filename, _ = self._decode_filename(data, offset=6)
        return filename, filesize

    def parse_request_download(self, data: bytes) -> str:
        filename, _ = self._decode_filename(data, offset=2)
        return filename

    def parse_response_filesize(self, data: bytes) -> int:
        return int.from_bytes(data[2:6], byteorder="big")

    def parse_err_code(self, data: bytes) -> CodError:
        return CodError(data[1])

    def parse_data_chunk(self, data: bytes) -> tuple[bytes, bool]:
        """Retorna (chunk_bytes, more)."""
        more = data[1] == 1
        return data[2:], more

    def parse_file_data(self, data: bytes) -> bytes:
        """Compatibilidad: extrae payload del primer (y único) chunk."""
        chunk, _ = self.parse_data_chunk(data)
        return chunk

    # ------------------------------------------------------------------
    # Helpers de fragmentación para uso en request/response
    # ------------------------------------------------------------------

    def chunks(self, file_data: bytes) -> list[tuple[bytes, bool]]:
        """Divide file_data en (chunk, more) listos para enviar."""
        size = self.MAX_CHUNK_BYTES
        parts = [file_data[i:i+size] for i in range(0, max(len(file_data), 1), size)]
        return [(part, i < len(parts) - 1) for i, part in enumerate(parts)]

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _encode_filename(self, filename: str) -> bytes:
        encoded = filename.encode("utf-8")
        length = len(encoded)
        if length > self.MAX_FILENAME_LENGTH:
            raise ValueError(f"Nombre de archivo demasiado largo: {length} bytes")
        return bytes([length]) + encoded

    def _decode_filename(self, data: bytes, offset: int) -> tuple[str, int]:
        length = data[offset]
        name = data[offset + 1: offset + 1 + length].decode("utf-8")
        return name, offset + 1 + length
