import queue

from app.codigos.cod_msj import CodMsj
from app.codigos.cod_op import CodOp
from app.msj_serializer import MessageSerializer
from app.rdt.stop_and_wait import StopAndWait
from app.response.download import ResponseDownload
from app.response.upload import ResponseUpload


class ClientHandler:
    def __init__(self, sk, addr, store):
        self.sk = sk
        self.addr = addr
        self.store = store

        # Dependencias extras...
        self._inbox = queue.Queue()
        self._rdt = StopAndWait(sk, addr, inbox=self._inbox)
        self._serializer = MessageSerializer()

    def handle(self, data):
        self._inbox.put((data, self.addr))
        raw = self._peek_raw(data)

        if raw is None:
            return

        msg_type, op = raw

        if msg_type != CodMsj.REQUEST:
            return

        if op == CodOp.UPLOAD:
            ResponseUpload(self._rdt, self._serializer, self.store).ejecutar()
        elif op == CodOp.DOWNLOAD:
            ResponseDownload(self._rdt, self._serializer, self.store).ejecutar()

    def receive(self, data):
        self._inbox.put((data, self.addr))

    def _peek_raw(self, data: bytes):
        HEADER_SIZE = 4
        if len(data) < HEADER_SIZE + 2:
            return None
        payload = data[HEADER_SIZE:]
        try:
            msg_type = CodMsj(payload[0])
            op = CodOp(payload[1])
            return msg_type, op
        except ValueError:
            return None
