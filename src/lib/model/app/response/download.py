from model.codigos.cod_error import CodError
from model.codigos.cod_msj import CodMsj
from model.app.messages.data_chunk import DataChunkMsg
from model.app.messages.err import ErrMsg
from model.app.messages.msg_type import peek_type
from model.app.messages.request_download import RequestDownloadMsg
from model.app.messages.response_filesize import ResponseFilesizeMsg
from model.rdt.rdt import RDTProtocol


class ResponseDownload:
    """
    Lado servidor del protocolo de download.
    Solo conoce mensajes de aplicación; ignora UDP, segmentos, etc.
    """

    def __init__(self, rdt: RDTProtocol, storage_dir: str) -> None:
        self._rdt         = rdt
        self._storage_dir = storage_dir

    def ejecutar(self, first_msg: bytes) -> None:
        # 1. Parsear REQUEST (ya recibido por SessionDispatcher)
        request  = RequestDownloadMsg.from_bytes(first_msg)
        filepath = f"{self._storage_dir}/{request.filename}"

        # 2. Verificar que el archivo existe
        file_data = self._leer_archivo(filepath)
        if file_data is None:
            self._rdt.enviar_mensaje(ErrMsg(CodError.FILE_NOT_FOUND).to_bytes())
            return

        # 3. Enviar RESPONSE con filesize
        self._rdt.enviar_mensaje(ResponseFilesizeMsg(filesize=len(file_data)).to_bytes())

        # 4. Esperar confirmación del cliente
        confirm = self._rdt.recibir_mensaje()
        if peek_type(confirm) == CodMsj.ERR:
            return

        # 5. Enviar DATA en chunks
        for chunk in DataChunkMsg.split_file(file_data):
            self._rdt.enviar_mensaje(chunk.to_bytes())

    def _leer_archivo(self, filepath: str) -> bytes | None:
        try:
            with open(filepath, "rb") as f:
                return f.read()
        except FileNotFoundError:
            return None
