import socket

from model.rdt.udp import UDPBase
from model.rdt.stop_and_wait.segment import Segment
from model.rdt.selective_repeat.window import SRWindow
from model.rdt.selective_repeat.timer import SRTimerManager
from model.rdt.selective_repeat.buffer import SRBuffer

WINDOW_SIZE  = 8
MAX_SEQ      = 16
TIMEOUT      = 0.5
MAX_INTENTOS = 50


class SelectiveRepeat(UDPBase):
    def __init__(self, sock, addr, inbox=None):
        super().__init__(sock, addr, inbox)
        self._window         = SRWindow(WINDOW_SIZE, MAX_SEQ)
        self._timers         = SRTimerManager(TIMEOUT)
        self._buffer         = SRBuffer(MAX_SEQ)
        self._acked: set[int] = set()
        self._next_seq       = 0
        self._sent_payloads: dict[int, bytes] = {}

    # ------------------------------------------------------------------
    # Interfaz pública
    # ------------------------------------------------------------------

    def enviar_mensaje(self, data: bytes) -> None:
        seq = self._next_seq

        # Esperar lugar en la ventana procesando ACKs mientras tanto
        intentos = 0
        while not self._window.in_window(seq):
            self._poll_acks()
            self._retransmitir_expirados()
            intentos += 1
            if intentos > MAX_INTENTOS:
                raise RuntimeError(
                    f"Ventana llena sin ACKs tras {MAX_INTENTOS} intentos"
                )

        # Guardar payload para posible retransmisión
        self._sent_payloads[seq] = data

        # Enviar
        seg = Segment(seq, 0, data)
        self._sock.sendto(seg.to_bytes(), self._addr)
        self._timers.start(seq)
        self._next_seq = (self._next_seq + 1) % MAX_SEQ

        # Drenar ACKs disponibles sin bloquearse
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

            ack_seg = Segment(0, seg.seq, b"")
            self._sock.sendto(ack_seg.to_bytes(), addr)

            if (seg.seq - self._buffer.base) % MAX_SEQ < WINDOW_SIZE:
                self._buffer.add(seg.seq, seg.payload)
                result = self._buffer.pop_in_order()
                if result is not None:
                    return result

    # ------------------------------------------------------------------
    # Privados
    # ------------------------------------------------------------------

    def _poll_acks(self) -> None:
        """Lee un ACK disponible sin bloquearse (timeout corto)."""
        try:
            data, _ = self._recv_raw()
        except (TimeoutError, socket.timeout, OSError):
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
                self._sock.sendto(seg.to_bytes(), self._addr)
                self._timers.start(seq)
