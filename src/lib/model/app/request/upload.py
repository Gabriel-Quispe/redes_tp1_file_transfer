from pathlib import Path

from model.app.messages.data_chunk import DataChunkMsg
from model.app.messages.err import ErrMsg
from model.app.messages.msg_type import peek_type
from model.app.messages.request_upload import RequestUploadMsg
from model.codigos.cod_error import CodError
from model.codigos.cod_msj import CodMsj
from model.codigos.cod_protocol import CodProtocol
from model.rdt.rdt import RDTProtocol


class RequestUpload:
    """
    Lado cliente del protocolo de upload.
    Solo conoce mensajes de aplicación; ignora UDP, segmentos, etc.
    """

    def __init__(
        self,
        rdt: RDTProtocol,
        filepath: str,
        filename: str = None,
        protocol: CodProtocol = CodProtocol.STOP_AND_WAIT,
    ) -> None:
        self._rdt = rdt
        self._filepath = filepath
        self._filename = filename if filename is not None else filepath.split("/")[-1]
        self._protocol = protocol

    def ejecutar(self) -> None:
        file_data = self._leer_archivo()

        # 1. Enviar REQUEST
        self._rdt.enviar_mensaje(
            RequestUploadMsg(
                protocol=self._protocol,
                filename=self._filename,
                filesize=len(file_data),
            ).to_bytes()
        )

        # 2. Esperar OK del servidor
        self._esperar_ok()

        # 3. Enviar DATA en chunks
        for chunk in DataChunkMsg.split_file(file_data):
            self._rdt.enviar_mensaje(chunk.to_bytes())

        # 4. Esperar confirmación final
        self._esperar_ok()

    def cancelar(self) -> None:
        self._rdt.enviar_mensaje(ErrMsg(CodError.USER_CANCELLED).to_bytes())

    # ------------------------------------------------------------------
    # Privados
    # ------------------------------------------------------------------

    def _leer_archivo(self) -> bytes:
        try:
            with Path(self._filepath).open("rb") as f:
                return f.read()
        except FileNotFoundError as err:
            raise FileNotFoundError(f"File does not exist: {self._filepath}") from err

    def _esperar_ok(self) -> None:
        try:
            data = self._rdt.recibir_mensaje()
        except (TimeoutError, OSError, RuntimeError) as e:
            raise RuntimeError("No se pudo entregar el mensaje") from e

        msg_type = peek_type(data)

        if msg_type == CodMsj.ERR:
            err = ErrMsg.from_bytes(data)
            raise RuntimeError(f"El servidor reportó un error: {err.code.name}")

        if msg_type != CodMsj.RESPONSE:
            raise RuntimeError("Respuesta inesperada del servidor")
