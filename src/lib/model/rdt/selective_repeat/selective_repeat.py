import socket

from model.rdt.udp import UDPBase
from model.rdt.stop_and_wait.segment import Segment
from model.rdt.selective_repeat.window import SRWindow
from model.rdt.selective_repeat.timer import SRTimerManager
from model.rdt.selective_repeat.buffer import SRBuffer

WINDOW_SIZE = 8
MAX_SEQ     = 16
TIMEOUT     = 1.0


class SelectiveRepeat(UDPBase):
    def __init__(self, sock, addr, inbox=None):
        super().__init__(sock, addr, inbox)

        self._window  = SRWindow(WINDOW_SIZE, MAX_SEQ)
        self._timers  = SRTimerManager(TIMEOUT)
        self._buffer  = SRBuffer(MAX_SEQ)
        self._acked: set[int] = set()

        self._next_seq = 0

    def enviar_mensaje(self, data: bytes) -> None:
        while not self._window.in_window(self._next_seq):
            self._handle_acks()

        seg = Segment(self._next_seq, 0, data)
        self._sock.sendto(seg.to_bytes(), self._addr)

        self._timers.start(self._next_seq)
        self._next_seq = (self._next_seq + 1) % MAX_SEQ

        self._handle_acks()

    def recibir_mensaje(self) -> bytes:
        while True:
            data, addr = self._recv_raw()

            seg = Segment.from_bytes(data)
            if not seg:
                continue

            ack_seg = Segment(0, seg.seq, b"")
            self._sock.sendto(ack_seg.to_bytes(), addr)

            if (seg.seq - self._buffer.base) % MAX_SEQ < WINDOW_SIZE:
                self._buffer.add(seg.seq, seg.payload)
                result = self._buffer.pop_in_order()
                if result is not None:
                    return result

    def _handle_acks(self):
        try:
            data, _ = self._recv_raw()
        except (TimeoutError, socket.timeout, OSError):
            for seq in self._timers.expired():
                seg = Segment(seq, 0, b"")
                self._sock.sendto(seg.to_bytes(), self._addr)
                self._timers.start(seq)
            return

        seg = Segment.from_bytes(data)
        if not seg:
            return

        ack = seg.ack
        self._timers.ack(ack)
        self._acked.add(ack)
        self._window.slide(self._acked)
