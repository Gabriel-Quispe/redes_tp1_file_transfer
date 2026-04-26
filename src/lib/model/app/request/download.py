from model.codigos.cod_error import CodError
from model.codigos.cod_msj import CodMsj
from model.codigos.cod_protocol import CodProtocol
from model.app.messages.data_chunk import DataChunkMsg
from model.app.messages.err import ErrMsg
from model.app.messages.msg_type import peek_type
from model.app.messages.request_download import RequestDownloadMsg
from model.app.messages.response_ok import ResponseOkMsg
from model.app.messages.response_filesize import ResponseFilesizeMsg
from model.rdt.rdt import RDTProtocol


class RequestDownload:
    """
    Lado cliente del protocolo de download.
    Solo conoce mensajes de aplicación; ignora UDP, segmentos, etc.
    """

    def __init__(
        self,
        rdt: RDTProtocol,
        filename: str,
        dest_path: str,
        protocol: CodProtocol = CodProtocol.STOP_AND_WAIT,
    ) -> None:
        self._rdt       = rdt
        self._filename  = filename
        self._dest_path = dest_path
        self._protocol  = protocol

    def ejecutar(self) -> None:
        # 1. Enviar REQUEST
        self._rdt.enviar_mensaje(
            RequestDownloadMsg(protocol=self._protocol, filename=self._filename).to_bytes()
        )

        # 2. Recibir RESPONSE con filesize
        data = self._rdt.recibir_mensaje()
        if peek_type(data) == CodMsj.ERR:
            err = ErrMsg.from_bytes(data)
            raise RuntimeError(f"El servidor reportó un error: {err.code.name}")

        response = ResponseFilesizeMsg.from_bytes(data)

        # 3. Confirmar al servidor (o cancelar si no hay espacio)
        error = self._validar_espacio(response.filesize)
        if error:
            self._rdt.enviar_mensaje(ErrMsg(error).to_bytes())
            return

        self._rdt.enviar_mensaje(ResponseOkMsg().to_bytes())

        # 4. Recibir DATA en chunks
        chunks = []
        while True:
            incoming  = self._rdt.recibir_mensaje()
            chunk_msg = DataChunkMsg.from_bytes(incoming)
            chunks.append(chunk_msg.payload)
            if not chunk_msg.more:
                break

        self._guardar_archivo(b"".join(chunks))

    def _validar_espacio(self, _filesize: int):
        return None  # Extender si se necesita verificar disco

    def _guardar_archivo(self, data: bytes) -> None:
        with open(self._dest_path, "wb") as f:
            f.write(data)
