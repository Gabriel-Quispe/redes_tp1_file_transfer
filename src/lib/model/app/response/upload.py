from pathlib import Path

from model.app.messages.data_chunk import DataChunkMsg
from model.app.messages.err import ErrMsg
from model.app.messages.msg_type import peek_type
from model.app.messages.request_upload import RequestUploadMsg
from model.app.messages.response_ok import ResponseOkMsg
from model.codigos.cod_error import CodError
from model.codigos.cod_msj import CodMsj
from model.rdt.rdt import RDTProtocol


class ResponseUpload:
    """
    Lado servidor del protocolo de upload.
    Solo conoce mensajes de aplicación; ignora UDP, segmentos, etc.
    """

    def __init__(self, rdt: RDTProtocol, storage_dir: str) -> None:
        self._rdt = rdt
        self._storage_dir = storage_dir

    def ejecutar(self, first_msg: bytes) -> None:
        # 1. Parsear REQUEST (ya recibido por SessionDispatcher)
        request = RequestUploadMsg.from_bytes(first_msg)

        # 2. Validar y responder
        error = self._validar(request.filename, request.filesize)
        if error:
            self._rdt.enviar_mensaje(ErrMsg(error).to_bytes())
            return

        self._rdt.enviar_mensaje(ResponseOkMsg().to_bytes())

        # 3. Recibir DATA en chunks
        chunks = []
        try:
            while True:
                incoming = self._rdt.recibir_mensaje()
                if peek_type(incoming) == CodMsj.ERR:
                    return  # cliente canceló

                chunk_msg = DataChunkMsg.from_bytes(incoming)
                chunks.append(chunk_msg.payload)
                if not chunk_msg.more:
                    break
        except RuntimeError:
            return  # cliente se desconectó

        file_data = b"".join(chunks)

        # 4. Escribir y confirmar
        dest_path = f"{self._storage_dir}/{request.filename}"
        write_error = self._escribir_archivo(dest_path, file_data, request.filesize)

        if write_error:
            self._rdt.enviar_mensaje(ErrMsg(write_error).to_bytes())
        else:
            self._rdt.enviar_mensaje(ResponseOkMsg().to_bytes())

    def _validar(self, filename: str, _filesize: int) -> CodError | None:
        if not filename or "/" in filename or "\\" in filename or ".." in filename:
            return CodError.INVALID_FILENAME
        return None

    def _escribir_archivo(self, path: str, data: bytes, expected_size: int) -> CodError | None:
        if len(data) != expected_size:
            return CodError.FILESIZE_MISMATCH
        try:
            with Path(path).open("wb") as f:
                f.write(data)
        except OSError:
            return CodError.WRITE_ERROR
        return None
