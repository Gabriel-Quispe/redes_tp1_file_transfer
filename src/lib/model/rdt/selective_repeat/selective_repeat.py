from model.rdt.selective_repeat.buffer import SRBuffer
from model.rdt.selective_repeat.timer import SRTimerManager
from model.rdt.selective_repeat.window import SRWindow
from model.rdt.stop_and_wait.segment import Segment
from model.rdt.udp import UDPBase

WINDOW_SIZE = 8
MAX_SEQ = 16
TIMEOUT = 0.5
MAX_INTENTOS = 50


class SelectiveRepeat(UDPBase):
    def __init__(self, sock, addr, inbox=None):
        super().__init__(sock, addr, inbox)
        self._window = SRWindow(WINDOW_SIZE, MAX_SEQ)
        self._timers = SRTimerManager(TIMEOUT)
        self._buffer = SRBuffer(MAX_SEQ)
        self._acked: set[int] = set()
        self._next_seq = 0
        self._sent_payloads: dict[int, bytes] = {}

    def enviar_mensaje(self, data: bytes) -> None:
        seq = self._next_seq

        intentos = 0
        while not self._window.in_window(seq):
            self._poll_acks()
            self._retransmitir_expirados()
            intentos += 1
            if intentos > MAX_INTENTOS:
                raise RuntimeError(f"Ventana llena sin ACKs tras {MAX_INTENTOS} intentos")

        self._sent_payloads[seq] = data

        seg = Segment(seq, 0, data)
        self._sendto(seg.to_bytes(), self._addr)
        self._timers.start(seq)
        self._next_seq = (self._next_seq + 1) % MAX_SEQ

        self._poll_acks()
        self._retransmitir_expirados()
        self._window.slide(self._acked)

    def recibir_mensaje(self) -> bytes:
        while True:
            try:
                data, addr = self._recv_raw()
            except TimeoutError:
                continue

            seg = Segment.from_bytes(data)
            if not seg:
                continue

            self._sendto(Segment(0, seg.seq, b"").to_bytes(), addr)

            if (seg.seq - self._buffer.base) % MAX_SEQ < WINDOW_SIZE:
                self._buffer.add(seg.seq, seg.payload)
                result = self._buffer.pop_in_order()
                if result is not None:
                    return result

    def _poll_acks(self) -> None:
        try:
            data, _ = self._recv_raw()
        except (TimeoutError, OSError):
            return

        seg = Segment.from_bytes(data)
        if not seg:
            return

        self._timers.ack(seg.ack)
        self._acked.add(seg.ack)
        self._sent_payloads.pop(seg.ack, None)
        self._window.slide(self._acked)

    def _retransmitir_expirados(self) -> None:
        for seq in self._timers.expired():
            if seq in self._sent_payloads:
                seg = Segment(seq, 0, self._sent_payloads[seq])
                self._sendto(seg.to_bytes(), self._addr)
                self._timers.start(seq)
