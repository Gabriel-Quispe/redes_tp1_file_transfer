import threading
import socket
import time
from typing import Dict, Optional, Tuple

from lib.protocol_strategies.protocol_strategy import ProtocolStrategy
from lib.segment import Segment
from lib.logger import logger
import lib.const as const


class SelectiveRepeat(ProtocolStrategy):
    def __init__(self, address, socket):
        super().__init__(address, socket)
        self.wsize = const.SV_MAX_WIN
        self.recv_buffer: Dict[int, Segment] = {}
        self._window: Dict[int, dict] = {}
        self._lock = threading.Lock()
        self._abort_event = threading.Event()
        self._ack_event = threading.Event()
        self._last_ack = None
        self._recv_thread = None

    def set_window(self, tam: int):
        self.wsize = max(const.SV_CLIENT_MIN_WIN, tam)

    def _start_recv_thread(self):
        """Arranca el hilo receptor de ACKs si no está corriendo."""
        if self._recv_thread is not None and self._recv_thread.is_alive():
            return
        self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._recv_thread.start()

    def _recv_loop(self):
        """Hilo que recibe ACKs continuamente mientras hay segmentos en vuelo."""
        while True:
            with self._lock:
                if not self._window:
                    break
            try:
                self.socket.settimeout(const.TIMEOUT * 2)
                raw_data, _ = self.socket.recvfrom(self.receive_tam)
                ack_pkt = Segment.unpack(raw_data)
            except (socket.timeout, ValueError):
                with self._lock:
                    if not self._window:
                        break
                continue
            except OSError:
                break

            if ack_pkt.opcode != const.OP_ACK:
                continue

            seq_acked = ack_pkt.seq_num
            with self._lock:
                if seq_acked in self._window and not self._window[seq_acked]["acked"]:
                    logger.debug(f"[SR] ACK recibido para seq={seq_acked}")
                    self._window[seq_acked]["acked"] = True
                    self._window[seq_acked]["timer"].cancel()
                    self._last_ack = ack_pkt
            self._ack_event.set()

    def _send_one(self, seq: int, max_retry: Optional[int]):
        with self._lock:
            if seq not in self._window or self._window[seq]["acked"]:
                return
            seg = self._window[seq]["segment"]
            retries = self._window[seq]["retries"]

        if max_retry is not None and retries >= max_retry:
            logger.debug(f"[SR] Max reintentos alcanzados para seq={seq}, abortando")
            self._abort_event.set()
            return

        logger.debug(f"[SR] Retransmitiendo seq={seq} (intento {retries + 1})")
        self.socket.sendto(seg.pack(), self.address)

        with self._lock:
            if seq in self._window and not self._window[seq]["acked"]:
                self._window[seq]["retries"] += 1
                t = threading.Timer(const.TIMEOUT, self._send_one, args=[seq, max_retry])
                t.daemon = True
                self._window[seq]["timer"] = t
                t.start()

    def send_data(self, segment: Segment, max_retry: Optional[int] = None) -> Optional[Segment]:
        """Envía un segmento con la lógica de Selective Repeat.

        La ventana es compartida entre llamadas, permitiendo tener múltiples
        segmentos en vuelo simultáneamente.

        max_retry sólo se usa al cerrar la conexión (OP_END).
        """
        if max_retry is not None:
            while True:
                with self._lock:
                    pending = {k: v for k, v in self._window.items() if not v["acked"]}
                    if not pending:
                        break
                self._ack_event.wait(timeout=const.TIMEOUT)
                self._ack_event.clear()

        base_seq = self.next_seq
        segment.seq_num = base_seq
        self.next_seq += 1

        while True:
            if self._abort_event.is_set():
                raise ConnectionError("Cerrando conexión")
            with self._lock:
                in_flight = sum(1 for v in self._window.values() if not v["acked"])
                if in_flight < self.wsize:
                    break
            self._ack_event.wait(timeout=const.TIMEOUT)
            self._ack_event.clear()

        t = threading.Timer(const.TIMEOUT, self._send_one, args=[base_seq, max_retry])
        t.daemon = True
        with self._lock:
            self._window[base_seq] = {
                "segment": segment,
                "acked": False,
                "retries": 0,
                "timer": t,
            }

        logger.debug(f"[SR] Envío inicial seq={base_seq}")
        self.socket.sendto(segment.pack(), self.address)
        t.start()

        self._start_recv_thread()

        if max_retry is not None:
            while True:
                if self._abort_event.is_set():
                    with self._lock:
                        for entry in self._window.values():
                            entry["timer"].cancel()
                    raise ConnectionError("Cerrando conexión")
                with self._lock:
                    if self._window.get(base_seq, {}).get("acked", False):
                        break
                self._ack_event.wait(timeout=const.TIMEOUT)
                self._ack_event.clear()

        return self._last_ack


    def receive_data(self) -> Tuple[int, Optional[bytes]]:
        """Recibe datos con reordenamiento de Selective Repeat.

        Usa self.recv_buffer (persistente entre llamadas) para guardar
        paquetes llegados fuera de orden. Entrega a la capa superior
        siempre en orden secuencial.
        """
        self.socket.settimeout(None)

        while True:

            if self.next_seq in self.recv_buffer:
                seg = self.recv_buffer.pop(self.next_seq)
                logger.debug(f"[SR] Entregando desde buffer seq={seg.seq_num}")
                self.next_seq += 1
                return (const.OP_DATA, seg.payload)

            try:
                raw_data, addr = self.socket.recvfrom(self.receive_tam)
                if addr != self.address:
                    continue
                segment = Segment.unpack(raw_data)
            except ValueError as e:
                logger.debug(f"[SR] Paquete descartado (checksum/tamaño): {e}")
                continue

            seq = segment.seq_num

            if segment.opcode == const.OP_END:
                logger.info("[SR] Fin de transmisión recibido.")
                ack = Segment(const.OP_ACK, seq, self.wsize, b"")
                self.socket.sendto(ack.pack(), self.address)
                return (const.OP_END, None)

            if segment.opcode == const.OP_ERROR:
                ack = Segment(const.OP_ACK, seq, self.wsize, b"")
                self.socket.sendto(ack.pack(), self.address)
                return (const.OP_ERROR, segment.payload)

            if segment.opcode != const.OP_DATA:
                logger.debug(f"[SR] Opcode inesperado {segment.opcode}, ignorando")
                continue

            ack = Segment(const.OP_ACK, seq, self.wsize, b"")
            self.socket.sendto(ack.pack(), self.address)

            if seq < self.next_seq:
                logger.debug(f"[SR] Duplicado seq={seq}, descartado")
                continue

            if seq >= self.next_seq + self.wsize:
                logger.debug(
                    f"[SR] seq={seq} fuera de ventana "
                    f"[{self.next_seq}, {self.next_seq + self.wsize}), descartado"
                )
                continue

            if seq not in self.recv_buffer:
                logger.debug(f"[SR] Buffereando seq={seq}")
                self.recv_buffer[seq] = segment

            if seq == self.next_seq:
                seg = self.recv_buffer.pop(self.next_seq)
                logger.debug(f"[SR] Entregando seq={seg.seq_num}")
                self.next_seq += 1
                return (const.OP_DATA, seg.payload)