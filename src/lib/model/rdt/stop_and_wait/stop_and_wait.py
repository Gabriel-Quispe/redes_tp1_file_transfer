from model.rdt.udp import UDPBase
from model.rdt.stop_and_wait.segment import Segment

MAX_INTENTOS = 3


class StopAndWait(UDPBase):
    def __init__(self, sock, addr, inbox=None):
        super().__init__(sock, addr, inbox)
        self._seq_tx = 0
        self._seq_rx = 0

    def enviar_mensaje(self, data: bytes) -> None:
        seg = Segment(self._seq_tx, 0, data)

        for _ in range(MAX_INTENTOS):
            self.send_segment(seg)

            if self._esperar_ack(self._seq_tx):
                self._seq_tx ^= 1
                return

        raise RuntimeError("Fallo en envío (StopAndWait)")

    def recibir_mensaje(self) -> bytes:
        for _ in range(MAX_INTENTOS):
            try:
                seg, addr = self.receive_segment()
            except TimeoutError:
                continue
            if not seg:
                continue

            ack = Segment(0, seg.seq, b"")
            self.send_segment(ack)

            if seg.seq == self._seq_rx:
                self._seq_rx ^= 1
                return seg.payload

        raise RuntimeError("Fallo en recepción")

    def _esperar_ack(self, expected: int) -> bool:
        try:
            seg, _ = self.receive_segment()
        except Exception:
            return False

        return seg and seg.ack == expected
