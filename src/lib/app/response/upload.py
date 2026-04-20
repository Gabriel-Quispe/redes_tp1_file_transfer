from app.codigos.cod_error import CodError
from app.codigos.cod_msj import CodMsj
from app.msj_serializer import MessageSerializer
from app.rdt.rdt import RDTProtocol


class ResponseUpload:
    def __init__(
        self, rdt: RDTProtocol, serializer: MessageSerializer, storage_dir: str
    ) -> None:
        self._rdt = rdt
        self._serializer = serializer
        self._storage_dir = storage_dir

    def ejecutar(self) -> None:
        # Paso 1: recibir REQUEST
        request = self._rdt.recibir_mensaje()
        filename, filesize = self._serializer.parse_request_upload(request)

        # Paso 2: validar y responder
        error = self._validar(filename, filesize)
        if error:
            self._rdt.enviar_mensaje(self._serializer.build_err(error))
            return

        self._rdt.enviar_mensaje(self._serializer.build_response_ok())

        # Paso 3: recibir DATA en chunks
        chunks = []
        try:
            while True:
                incoming = self._rdt.recibir_mensaje()
                msg_type = self._serializer.parse_type(incoming)

                if msg_type == CodMsj.ERR:
                    return  # cliente canceló

                chunk, more = self._serializer.parse_data_chunk(incoming)
                chunks.append(chunk)
                if not more:
                    break
        except RuntimeError:
            return  # cliente se desconectó durante la transferencia

        file_data = b"".join(chunks)

        # Paso 4: escribir y confirmar
        dest_path = f"{self._storage_dir}/{filename}"
        write_error = self._escribir_archivo(dest_path, file_data, filesize)

        if write_error:
            self._rdt.enviar_mensaje(self._serializer.build_err(write_error))
        else:
            self._rdt.enviar_mensaje(self._serializer.build_response_ok())

    def _validar(self, filename: str, _filesize: int) -> CodError | None:
        if not filename or "/" in filename or "\\" in filename or ".." in filename:
            return CodError.INVALID_FILENAME
        return None

    def _escribir_archivo(
        self, path: str, data: bytes, expected_size: int
    ) -> CodError | None:
        if len(data) != expected_size:
            return CodError.FILESIZE_MISMATCH
        try:
            with open(path, "wb") as f:
                f.write(data)
        except OSError:
            return CodError.WRITE_ERROR
        return None
