from model.app.messages.msg_type import peek_op, peek_type
from model.app.messages.request_download import RequestDownloadMsg
from model.app.messages.request_upload import RequestUploadMsg
from model.app.response.download import ResponseDownload
from model.app.response.upload import ResponseUpload
from model.codigos.cod_msj import CodMsj
from model.codigos.cod_op import CodOp
from model.rdt.router import RDTRouter


class AppRouter:
    def __init__(self, rdt: RDTRouter, store: str) -> None:
        self._rdt = rdt
        self._store = store

    def resolver(self, data: bytes) -> None:
        if peek_type(data) != CodMsj.REQUEST:
            return

        op = peek_op(data)

        if op == CodOp.UPLOAD:
            protocol = RequestUploadMsg.from_bytes(data).protocol
            self._rdt.set_protocol(protocol)
            ResponseUpload(self._rdt, self._store).ejecutar(data)

        elif op == CodOp.DOWNLOAD:
            protocol = RequestDownloadMsg.from_bytes(data).protocol
            self._rdt.set_protocol(protocol)
            ResponseDownload(self._rdt, self._store).ejecutar(data)
