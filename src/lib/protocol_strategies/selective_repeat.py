import threading
import socket
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

    def set_window(self, tam: int):
        self.wsize = max(const.SV_CLIENT_MIN_WIN, tam)
    def send_data(self, segment: Segment, max_retry: Optional[int] = None) -> Optional[Segment]:
        """Envía un segmento con la lógica de Selective Repeat.

        Cada segmento sin ACK tiene su propio timer. Cuando un timer expira
        sólo se retransmite ese segmento, no toda la ventana (a diferencia
        de Go-Back-N).

        max_retry sólo se usa al cerrar la conexión (OP_END), igual que en
        Stop & Wait, para evitar el problema de los dos ejércitos.
        """
        base_seq = self.next_seq
        segment.seq_num = base_seq
        self.next_seq += 1


        window: Dict[int, dict] = {}
        lock = threading.Lock()

        def _send_one(seq: int):
            with lock:
                if seq not in window or window[seq]["acked"]:
                    return
                seg = window[seq]["segment"]
                retries = window[seq]["retries"]

            if max_retry is not None and retries >= max_retry:
                raise ConnectionError("Cerrando conexión")

            logger.debug(f"[SR] Retransmitiendo seq={seq} (intento {retries + 1})")
            self.socket.sendto(seg.pack(), self.address)

            with lock:
                if seq in window and not window[seq]["acked"]:
                    window[seq]["retries"] += 1
                    t = threading.Timer(const.TIMEOUT, _send_one, args=[seq])
                    t.daemon = True
                    window[seq]["timer"] = t
                    t.start()

        t = threading.Timer(const.TIMEOUT, _send_one, args=[base_seq])
        t.daemon = True
        with lock:
            window[base_seq] = {
                "segment": segment,
                "acked": False,
                "retries": 0,
                "timer": t,
            }

        logger.debug(f"[SR] Envío inicial seq={base_seq}")
        self.socket.sendto(segment.pack(), self.address)
        t.start()

        last_ack = None
        while True:
            try:
                self.socket.settimeout(const.TIMEOUT * 4)
                raw_data, _ = self.socket.recvfrom(self.receive_tam)
                ack_pkt = Segment.unpack(raw_data)
            except (socket.timeout, ValueError):
                with lock:
                    if all(v["acked"] for v in window.values()):
                        break
                continue

            if ack_pkt.opcode != const.OP_ACK:
                continue

            seq_acked = ack_pkt.seq_num
            with lock:
                if seq_acked in window and not window[seq_acked]["acked"]:
                    logger.debug(f"[SR] ACK recibido para seq={seq_acked}")
                    window[seq_acked]["acked"] = True
                    window[seq_acked]["timer"].cancel()
                    last_ack = ack_pkt

                if all(v["acked"] for v in window.values()):
                    break

        with lock:
            for entry in window.values():
                entry["timer"].cancel()

        return last_ack



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
