from app.codigos.cod_error import CodError
from app.codigos.cod_msj import CodMsj
from app.msj_serializer import MessageSerializer
from app.rdt.rdt import RDTProtocol


class RequestDownload:
    def __init__(self, rdt: RDTProtocol, serializer: MessageSerializer,
                 filename: str, dest_path: str) -> None:
        self._rdt = rdt
        self._serializer = serializer
        self._filename = filename
        self._dest_path = dest_path

    def ejecutar(self) -> None:
        # Paso 1: enviar REQUEST
        self._rdt.enviar_mensaje(
            self._serializer.build_request_download(self._filename)
        )

        # Paso 2: recibir RESPONSE con filesize
        response = self._rdt.recibir_mensaje()
        msg_type = self._serializer.parse_type(response)

        if msg_type == CodMsj.ERR:
            code = self._serializer.parse_err_code(response)
            raise RuntimeError(f"El servidor reportó un error: {code.name}")

        filesize = self._serializer.parse_response_filesize(response)

        # Paso 3: confirmar al servidor
        error = self._validar_espacio(filesize)
        if error:
            self._rdt.enviar_mensaje(self._serializer.build_err(error))
            return

        self._rdt.enviar_mensaje(self._serializer.build_response_ok())

        # Paso 4: recibir DATA en chunks
        chunks = []
        while True:
            incoming = self._rdt.recibir_mensaje()
            chunk, more = self._serializer.parse_data_chunk(incoming)
            chunks.append(chunk)
            if not more:
                break

        self._guardar_archivo(b"".join(chunks))

    def _validar_espacio(self, _filesize: int) -> CodError | None:
        return None

    def _guardar_archivo(self, data: bytes) -> None:
        with open(self._dest_path, "wb") as f:
            f.write(data)
