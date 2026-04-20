import socket

from app.codigos.cod_error import CodError
from app.codigos.cod_msj import CodMsj
from app.msj_serializer import MessageSerializer
from app.rdt.rdt import RDTProtocol


class RequestUpload:
    def __init__(
        self,
        rdt: RDTProtocol,
        serializer: MessageSerializer,
        filepath: str,
        filename: str = None,
    ) -> None:
        self._rdt = rdt
        self._serializer = serializer
        self._filepath = filepath
        self._filename = filename if filename is not None else filepath.split("/")[-1]

    def ejecutar(self) -> None:
        file_data = self._leer_archivo()
        filesize = len(file_data)

        # Paso 1: REQUEST
        self._rdt.enviar_mensaje(
            self._serializer.build_request_upload(self._filename, filesize)
        )

        # Paso 2: esperar OK del servidor
        self._esperar_ok()

        # Paso 3: enviar DATA en chunks
        for chunk, more in self._serializer.chunks(file_data):
            self._rdt.enviar_mensaje(self._serializer.build_data_chunk(chunk, more))

        # Paso 4: esperar confirmación final
        self._esperar_ok()

    def cancelar(self) -> None:
        self._rdt.enviar_mensaje(self._serializer.build_err(CodError.USER_CANCELLED))

    def _leer_archivo(self) -> bytes:
        try:
            with open(self._filepath, "rb") as f:
                return f.read()
        except FileNotFoundError as err:
            raise FileNotFoundError(f"File does not exist: {self._filepath}") from err

    def _esperar_ok(self) -> None:
        try:
            response = self._rdt.recibir_mensaje()
        except (TimeoutError, socket.timeout, OSError):
            raise RuntimeError("No se pudo entregar el mensaje")

        if not response:
            raise RuntimeError("No se pudo entregar el mensaje")

        try:
            msg_type = self._serializer.parse_type(response)
        except Exception:
            raise RuntimeError("No se pudo entregar el mensaje")

        if msg_type == CodMsj.ERR:
            code = self._serializer.parse_err_code(response)
            raise RuntimeError(f"El servidor reportó un error: {code.name}")

        if msg_type != CodMsj.RESPONSE:
            raise RuntimeError("No se pudo entregar el mensaje")
