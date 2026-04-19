from app.codigos.cod_error import CodError
from app.codigos.cod_msj import CodMsj
from app.msj_serializer import MessageSerializer
from app.rdt import RDTProtocol


class RequestDownload:
    """
    Orquesta la operación DOWNLOAD desde el lado del cliente.

    Flujo:
        cliente → REQUEST { DOWNLOAD, filename }
        cliente ← RESPONSE { OK, filesize }
        cliente → RESPONSE { OK }
        cliente ← DATA { <bytes crudos> }
    """

    def __init__(
        self,
        rdt: RDTProtocol,
        serializer: MessageSerializer,
        filename: str,
        dest_path: str,
    ) -> None:
        self._rdt = rdt
        self._serializer = serializer
        self._filename = filename
        self._dest_path = dest_path

    def ejecutar(self) -> None:
        # Paso 1: enviar REQUEST
        request = self._serializer.build_request_download(self._filename)
        self._rdt.enviar_mensaje(request)

        # Paso 2: recibir RESPONSE con filesize
        response = self._rdt.recibir_mensaje()
        msg_type = self._serializer.parse_type(response)

        if msg_type == CodMsj.ERR:
            code = self._serializer.parse_err_code(response)
            raise RuntimeError(f"El servidor reportó un error: {code.name}")

        filesize = self._serializer.parse_response_filesize(response)

        # Paso 3: validar espacio y confirmar
        error = self._validar_espacio(filesize)
        if error:
            self._rdt.enviar_mensaje(self._serializer.build_err(error))
            return

        self._rdt.enviar_mensaje(self._serializer.build_response_ok())

        # Paso 4: recibir DATA y guardar
        incoming = self._rdt.recibir_mensaje()
        file_data = self._serializer.parse_file_data(incoming)
        self._guardar_archivo(file_data)

    def _validar_espacio(self, _filesize: int) -> CodError | None:
        # Aquí se puede verificar espacio disponible en disco
        return None

    def _guardar_archivo(self, data: bytes) -> None:
        with open(self._dest_path, "wb") as f:
            f.write(data)
