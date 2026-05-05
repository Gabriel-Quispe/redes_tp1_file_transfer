import threading
import socket
import time
from typing import Dict, Optional, Tuple
from lib.protocol_strategies.protocol_strategy import ProtocolStrategy
from lib.segment import Segment
from lib.logger import logger
import lib.const as const


# Definimos los estados fuera o dentro, pero usémoslos consistentemente
class State:
    READY = 1
    IN_FLIGHT = 2
    ACKED = 3


class SelectiveRepeat(ProtocolStrategy):
    def __init__(self, address, socket):
        self.error_segment: Segment = None
        super().__init__(address, socket)
        self.closing = False
        self.last_acked: float = time.time()
        # self.active = True
        self.wsize = const.SV_MAX_WIN
        # Buffer de Recepción para ordenar los segmentos entrantes
        self.recv_buffer: Dict[int, Segment] = {}
        # Ventana de envio
        # {seq: {"seg": Segment,
        # "state": State,
        # "time_stamp": float,
        # "retry": int}}
        # buffer de envio, para retransmitir segmentos
        self.window_data: Dict[int, dict] = {}

        # Hilos
        self.ack_thread: Optional[threading.Thread] = None
        self.transmit_thread: Optional[threading.Thread] = None
        self.cond = threading.Condition(threading.Lock())
        self.max_recv_retry = 40

    def send_data(self, segment: Segment, max_retry: int = 40):
        self._wakeup_threads()
        with self.cond:
            while self.active:
                win_tam = self.base_seq + self.wsize
                # Si existe espacio: se envia el paquete
                if self.next_seq < win_tam:
                    segment.seq_num = self.next_seq
                    self.window_data[self.next_seq] = {
                        "seg": segment,
                        "state": State.IN_FLIGHT,
                        "time_stamp": time.time(),
                        "retry": max_retry,
                        "max_retry": max_retry,
                    }

                    is_op_end = ""
                    if segment.opcode == const.OP_END:
                        is_op_end = " PAQUETE END"
                    logger.debug(f"Envío paquete{is_op_end}: {self.next_seq}")
                    self.socket.sendto(segment.pack(), self.address)
                    self.next_seq += 1
                    return
                self.cond.wait(timeout=0.5)
        if not self.active:
            raise ConnectionError(
                "La conexión se cayó mientras se esperaba espacio en ventana"
            )

    def _retransmitter_loop(self):
        """Hilo Emisor: itera buscando paquetes con timer expirado"""
        while self.active:
            now = time.time()
            something_todo = False
            # si hay algo que enviar, pero no hay respuesta
            # por mucho tiempo, cortamos
            if self._is_connection_dead(now):
                self.active = False
                with self.cond:
                    self.cond.notify_all()
                break
            with self.cond:
                # Usamos list(keys) para poder borrar elementos sin error
                for seq in list(self.window_data.keys()):
                    if not self.active:
                        break
                    entry = self.window_data[seq]

                    if entry["state"] == State.IN_FLIGHT:
                        # Si pasó el tiempo de timeout
                        if now - entry["time_stamp"] > self.timeout:
                            something_todo = True  # ALGO QUE HACER
                            if entry["retry"] <= 0:
                                # Si estamos en proceso de cierre
                                # o el paquete es el fin, se sale
                                if self.closing:
                                    self.window_data.pop(seq, None)
                                    continue
                                # falló la conexión!
                                self.active = False
                                self.cond.notify_all()
                                break
                            if self.closing:
                                self.window_data.pop(seq, None)
                                continue
                            retries = entry["retry"]
                            msg = f"segmento seq={seq}"
                            logger.debug(f"{msg} quedan {retries} intentos)")
                            addr = self.address
                            self.socket.sendto(entry["seg"].pack(), addr)
                            entry["time_stamp"] = now
                            entry["retry"] -= 1
                if not something_todo:
                    self.cond.wait(timeout=self.timeout)

    def _receiver_loop(self):
        """consumidor que recibe paquetes del socket: maneja ACK, DATA, END"""
        while self.active:
            try:
                self.socket.settimeout(self.timeout)
                raw_data, addr = self.socket.recvfrom(self.receive_tam)
                if addr != self.address:
                    continue
                self.last_acked = time.time()
                segment = Segment.unpack(raw_data)
                with self.cond:
                    if segment.opcode == const.OP_ACK:
                        self._manage_ack(segment.seq_num)
                        continue
                    elif segment.opcode in [const.OP_DATA, const.OP_END]:
                        self._manage_data(segment)
                    elif segment.opcode == const.OP_ERROR:
                        self._handle_error(segment)
            except (socket.timeout, ValueError):
                continue
            except Exception:
                continue

    def receive_data(self) -> Tuple[int, Optional[bytes]]:
        """Lógica de recepción con buffer para paquetes fuera de orden
        esta función es bloqueante!
        """
        self._wakeup_threads()
        # tiempo del último paq recibido
        # tiempo maximo esperando cualquier paquete
        max_time_waiting = 2.0 + self.max_recv_retry * self.timeout
        # active se desactiva por stop_strategy() desde el rdtsocket
        # active solo se desactiva forzosamente si falla _retransmitter_loop()
        while self.active:
            with self.cond:
                if self.error_segment:
                    seg = self.error_segment
                    self.error_segment = None
                    return (seg.opcode, seg.payload)
                if self.recv_base_seq in self.recv_buffer:
                    seg = self.recv_buffer.pop(self.recv_base_seq)
                    self.recv_base_seq += 1
                    return (seg.opcode, seg.payload)
                self.cond.wait(timeout=self.timeout)

            if time.time() - self.last_acked > max_time_waiting:
                with self.cond:
                    self.error_segment = Segment(
                        const.OP_ERROR,
                        0,
                        self.wsize,
                        b"Conexion perdida: el emisor no responde",
                    )
                    self.active = False
                    self.cond.notify_all()
                    err_opcode = self.error_segment.opcode
                    return (err_opcode, self.error_segment.payload)

    def _slide_window(self):
        """Desliza la ventana eliminando los paquetes ACKED desde base_seq"""
        while (
            self.base_seq in self.window_data
            and self.window_data[self.base_seq]["state"] == State.ACKED
        ):
            del self.window_data[self.base_seq]
            self.base_seq += 1

    def _send_ack(self, seq: int):
        ack = Segment(const.OP_ACK, seq, self.wsize, b"")
        self.socket.sendto(ack.pack(), self.address)

    def _buff_segment(self, segment: Segment):
        """Guarda el segmento en el buffer
        si está dentro de la ventana de recepcion"""
        seq = segment.seq_num
        win_tam = self.recv_base_seq + self.wsize
        # si el seqnumber esta entre la base y el tamaño de ventana
        if self.recv_base_seq <= seq < win_tam:
            if seq not in self.recv_buffer:
                self.recv_buffer[seq] = segment
                logger.debug(f"Buffereado seq={seq}")

    def _manage_ack(self, seq: int) -> None:
        if seq in self.window_data:
            entry = self.window_data[seq]
            # RTO nuevo si no es de una retransmision
            if entry["retry"] == entry["max_retry"]:
                rtt = time.time() - entry["time_stamp"]
                self.set_timeout(rtt)
            entry["state"] = State.ACKED
            self._slide_window()
            self.cond.notify_all()

    def _manage_data(self, segment: Segment) -> None:
        win_tam = self.recv_base_seq + self.wsize
        seq = segment.seq_num
        # control de flujo
        if seq < win_tam:
            self._buff_segment(segment)
            self._send_ack(seq)
        else:
            reason = "Buffer lleno!"
            logger.debug(f"Paquete {seq} descartado{reason}")
        self.cond.notify_all()

    def _handle_error(self, segment: Segment) -> None:
        self.error_segment = segment
        self.active = False
        self.cond.notify_all()

    def stop_strategy(self):
        """Limpieza de hilos y recursos.
        Esto se llama en el socket cuando intentamos cerrar la conexion.
        """
        with self.cond:
            self.closing = True
            self.active = False
            self.window_data.clear()
            self.recv_buffer.clear()
            # si no despierto los threads no puedo hacer join
            self.cond.notify_all()
        if self.ack_thread:
            self.ack_thread.join(timeout=1)
        if self.transmit_thread:
            self.transmit_thread.join(timeout=1)

    def _is_connection_dead(self, time: float) -> bool:
        if not self.window_data:
            return False
        return (time - self.last_acked) > max(5.0, self.timeout * 4)

    def _wakeup_threads(self):
        """Despierta a los hilos para laburar"""
        if not self.active:
            return
        with self.cond:
            if self.ack_thread is None or not self.ack_thread.is_alive():
                self.active = True
                self.ack_thread = threading.Thread(
                    target=self._receiver_loop, daemon=True
                )
                self.transmit_thread = threading.Thread(
                    target=self._retransmitter_loop, daemon=True
                )
                self.transmit_thread.start()
                self.ack_thread.start()
