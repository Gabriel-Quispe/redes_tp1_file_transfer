from app.codigos.cod_error import CodError
from app.codigos.cod_msj import CodMsj
from app.msj_serializer import MessageSerializer
from app.rdt.rdt import RDTProtocol


class ResponseDownload:
    def __init__(
        self, rdt: RDTProtocol, serializer: MessageSerializer, storage_dir: str
    ) -> None:
        self._rdt = rdt
        self._serializer = serializer
        self._storage_dir = storage_dir

    def ejecutar(self) -> None:
        # Paso 1: recibir REQUEST
        request = self._rdt.recibir_mensaje()
        filename = self._serializer.parse_request_download(request)
        filepath = f"{self._storage_dir}/{filename}"

        # Paso 2: verificar archivo
        file_data = self._leer_archivo(filepath)
        if file_data is None:
            self._rdt.enviar_mensaje(
                self._serializer.build_err(CodError.FILE_NOT_FOUND)
            )
            return

        filesize = len(file_data)
        self._rdt.enviar_mensaje(self._serializer.build_response_ok_filesize(filesize))

        # Paso 3: esperar confirmación del cliente
        confirm = self._rdt.recibir_mensaje()
        if self._serializer.parse_type(confirm) == CodMsj.ERR:
            return

        # Paso 4: enviar DATA en chunks
        for chunk, more in self._serializer.chunks(file_data):
            self._rdt.enviar_mensaje(self._serializer.build_data_chunk(chunk, more))

    def _leer_archivo(self, filepath: str) -> bytes | None:
        try:
            with open(filepath, "rb") as f:
                return f.read()
        except FileNotFoundError:
            return None
