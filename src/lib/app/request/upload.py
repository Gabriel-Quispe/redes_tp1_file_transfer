from app.codigos.cod_error import CodError
from app.codigos.cod_msj import CodMsj
from app.msj_serializer import MessageSerializer
from app.rdt import RDTProtocol


class RequestUpload:
    """
    Orquesta la operación UPLOAD desde el lado del cliente.

    Flujo:
        cliente → REQUEST { UPLOAD, filename, filesize }
        cliente ← RESPONSE { OK }
        cliente → DATA { <bytes crudos> }
        cliente ← RESPONSE { OK }
    """

    def __init__(
        self,
        rdt: RDTProtocol,
        serializer: MessageSerializer,
        filepath: str,
    ) -> None:
        self._rdt = rdt
        self._serializer = serializer
        self._filepath = filepath

    def ejecutar(self) -> None:
        filename = self._filepath.split("/")[-1]
        file_data = self._leer_archivo()
        filesize = len(file_data)

        # Paso 1: enviar REQUEST
        request = self._serializer.build_request_upload(filename, filesize)
        self._rdt.enviar_mensaje(request)

        # Paso 2: esperar RESPONSE inicial del servidor
        self._esperar_ok()

        # Paso 3: enviar DATA
        data_msg = self._serializer.build_data(file_data)
        self._rdt.enviar_mensaje(data_msg)

        # Paso 4: esperar RESPONSE final del servidor
        self._esperar_ok()

    def cancelar(self) -> None:
        """Notifica al servidor que el cliente cancela la transferencia."""
        err_msg = self._serializer.build_err(CodError.USER_CANCELLED)
        self._rdt.enviar_mensaje(err_msg)

    def _leer_archivo(self) -> bytes:
        try:
            with open(self._filepath, "rb") as f:
                return f.read()
        except FileNotFoundError as err:
            raise FileNotFoundError(f"Archivo no encontrado: {self._filepath}") from err

    def _esperar_ok(self) -> None:
        response = self._rdt.recibir_mensaje()
        msg_type = self._serializer.parse_type(response)

        if msg_type == CodMsj.ERR:
            code = self._serializer.parse_err_code(response)
            raise RuntimeError(f"El servidor reportó un error: {code.name}")

        if msg_type != CodMsj.RESPONSE:
            raise RuntimeError(f"Tipo de mensaje inesperado: {msg_type}")
