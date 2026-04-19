import queue

from app.codigos.cod_msj import CodMsj
from app.codigos.cod_op import CodOp
from app.msj_serializer import MessageSerializer
from app.rdt.stop_and_wait import StopAndWait
from app.response.download import ResponseDownload
from app.response.upload import ResponseUpload


class ClientHandler:
    def __init__(self, sock, addr, storage):
        self.sock = sock
        self.addr = addr
        self.storage = storage
        self._inbox = queue.Queue()
        self._rdt = StopAndWait(sock, addr, inbox=self._inbox)
        self._serializer = MessageSerializer()

    def handle(self, data):
        """
        Punto de entrada del hilo. Recibe el primer mensaje del cliente
        y delega al transfer correspondiente (upload o download).
        """
        # Depositar el primer paquete en la cola para que el RDT lo consuma
        self._inbox.put((data, self.addr))

        # Leer el mensaje a nivel aplicación para saber qué operación es
        # Nota: usamos el serializer directo sobre `data` para no consumir
        # el mensaje de la cola — el RDT lo leerá cuando ejecute()  lo pida.
        # Sin embargo, como el RDT va a consumirlo, necesitamos peekear el
        # tipo ANTES de que el RDT lo consuma. Lo hacemos parseando el raw.
        raw = self._peek_raw(data)
        if raw is None:
            return  # paquete corrupto, ignorar

        msg_type, op = raw

        if msg_type != CodMsj.REQUEST:
            return  # primer mensaje debe ser siempre un REQUEST

        if op == CodOp.UPLOAD:
            ResponseUpload(self._rdt, self._serializer, self.storage).ejecutar()
        elif op == CodOp.DOWNLOAD:
            ResponseDownload(self._rdt, self._serializer, self.storage).ejecutar()

    def receive(self, data):
        """
        Recibe mensajes siguientes del mismo cliente durante la transferencia.
        Los deposita en la cola para que el RDT los consuma.
        """
        self._inbox.put((data, self.addr))

    def _peek_raw(self, data: bytes):
        """
        Extrae tipo de mensaje y operación del segmento RDT sin consumirlo.
        Retorna (CodMsj, CodOp) o None si el paquete es inválido.
        """
        # El segmento RDT tiene 4 bytes de header, luego el payload de aplicación
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
