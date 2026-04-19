from app.codigos.cod_error import CodError
from app.codigos.cod_msj import CodMsj
from app.codigos.cod_op import CodOp
from app.codigos.cod_state import CodState


class MessageSerializer:
    """
    Responsabilidad única: construir y parsear los mensajes
    binarios del protocolo de aplicación.

    No conoce sockets, no conoce archivos, no orquesta flujos.
    Solo sabe convertir estructuras de datos a bytes y viceversa.
    """

    MAX_FILENAME_LENGTH = 255

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------

    def build_request_upload(self, filename: str, filesize: int) -> bytes:
        # [TYPE(1)][OP(1)][filesize(4)][filename_len(1)][filename(N)]
        return (
            bytes([CodMsj.REQUEST, CodOp.UPLOAD])
            + filesize.to_bytes(4, byteorder="big")
            + self._encode_filename(filename)
        )

    def build_request_download(self, filename: str) -> bytes:
        # [TYPE(1)][OP(1)][filename_len(1)][filename(N)]
        return bytes([CodMsj.REQUEST, CodOp.DOWNLOAD]) + self._encode_filename(filename)

    def build_response_ok(self) -> bytes:
        # [TYPE(1)][STATE(1)]
        return bytes([CodMsj.RESPONSE, CodState.OK])

    def build_response_ok_filesize(self, filesize: int) -> bytes:
        # [TYPE(1)][STATE(1)][filesize(4)]
        return bytes([CodMsj.RESPONSE, CodState.OK]) + filesize.to_bytes(4, byteorder="big")

    def build_data(self, file_data: bytes) -> bytes:
        # [TYPE(1)][bytes crudos]
        return bytes([CodMsj.DATA]) + file_data

    def build_err(self, code: CodError) -> bytes:
        # [TYPE(1)][código(1)]
        return bytes([CodMsj.ERR, code])

    # ------------------------------------------------------------------
    # Parsers
    # ------------------------------------------------------------------

    def parse_type(self, data: bytes) -> CodMsj:
        return CodMsj(data[0])

    def parse_request_upload(self, data: bytes) -> tuple[str, int]:
        # [TYPE(1)][OP(1)][filesize(4)][filename_len(1)][filename(N)]
        filesize = int.from_bytes(data[2:6], byteorder="big")
        filename, _ = self._decode_filename(data, offset=6)
        return filename, filesize

    def parse_request_download(self, data: bytes) -> str:
        # [TYPE(1)][OP(1)][filename_len(1)][filename(N)]
        filename, _ = self._decode_filename(data, offset=2)
        return filename

    def parse_response_filesize(self, data: bytes) -> int:
        # [TYPE(1)][STATE(1)][filesize(4)]
        return int.from_bytes(data[2:6], byteorder="big")

    def parse_err_code(self, data: bytes) -> CodError:
        return CodError(data[1])

    def parse_file_data(self, data: bytes) -> bytes:
        # [TYPE(1)][bytes crudos]
        return data[1:]

    # ------------------------------------------------------------------
    # Helpers privados de codificación
    # ------------------------------------------------------------------

    def _encode_filename(self, filename: str) -> bytes:
        encoded = filename.encode("utf-8")
        length = len(encoded)
        if length > MessageSerializer.MAX_FILENAME_LENGTH:
            raise ValueError(
                f"Nombre de archivo demasiado largo: {length} bytes "
                f"(máx {MessageSerializer.MAX_FILENAME_LENGTH})"
            )
        return bytes([length]) + encoded

    def _decode_filename(self, data: bytes, offset: int) -> tuple[str, int]:
        length = data[offset]
        name = data[offset + 1 : offset + 1 + length].decode("utf-8")
        new_off = offset + 1 + length
        return name, new_off
