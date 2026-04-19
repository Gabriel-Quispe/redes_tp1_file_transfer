from app.codigos.cod_error import CodError
from app.codigos.cod_msj import CodMsj
from app.msj_serializer import MessageSerializer
from app.rdt.rdt import RDTProtocol


class ResponseDownload:
    """
    Atiende una operación DOWNLOAD desde el lado del servidor.

    Flujo:
        servidor ← REQUEST { DOWNLOAD, filename }
        servidor → RESPONSE { OK, filesize }
        servidor ← RESPONSE { OK }
        servidor → DATA { <bytes crudos> }
    """

    def __init__(
        self,
        rdt: RDTProtocol,
        serializer: MessageSerializer,
        storage_dir: str,
    ) -> None:
        self._rdt = rdt
        self._serializer = serializer
        self._storage_dir = storage_dir

    def ejecutar(self) -> None:
        # Paso 1: recibir REQUEST
        request = self._rdt.recibir_mensaje()
        filename = self._serializer.parse_request_download(request)
        filepath = f"{self._storage_dir}/{filename}"

        # Paso 2: verificar que existe y responder con filesize
        file_data = self._leer_archivo(filepath)
        if file_data is None:
            self._rdt.enviar_mensaje(self._serializer.build_err(CodError.FILE_NOT_FOUND))
            return

        filesize = len(file_data)
        self._rdt.enviar_mensaje(self._serializer.build_response_ok_filesize(filesize))

        # Paso 3: esperar confirmación del cliente
        confirm = self._rdt.recibir_mensaje()
        msg_type = self._serializer.parse_type(confirm)

        if msg_type == CodMsj.ERR:
            # el cliente no tiene espacio, abortamos
            return

        # Paso 4: enviar DATA
        data_msg = self._serializer.build_data(file_data)
        self._rdt.enviar_mensaje(data_msg)

    def _leer_archivo(self, filepath: str) -> bytes | None:
        try:
            with open(filepath, "rb") as f:
                return f.read()
        except FileNotFoundError:
            return None
