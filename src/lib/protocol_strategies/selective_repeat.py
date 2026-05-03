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
        super().__init__(address, socket)
        self.closing = False
        # self.active = True
        self.wsize = const.SV_MAX_WIN
        # Buffer de Recepción para ordenar los segmentos entrantes
        self.recv_buffer: Dict[int, Segment] = {}
        # Ventana de envio
        # {seq: {"seg": Segment,
        # "state": State,
        # "time_stamp": float,
        # "retry": int}}
        self.window_data: Dict[int, dict] = {}
        self.lock = threading.Lock()
        # Hilos
        self.ack_thread: Optional[threading.Thread] = None
        self.transmit_thread: Optional[threading.Thread] = None
        self.cond = threading.Condition(self.lock)
        self.max_recv_retry = 6

    def wakeup_threads(self):
        """Despierta a los hilos para laburar"""
        if not self.active:
            return
        with self.cond:
            if self.ack_thread is None or not self.ack_thread.is_alive():
                self.active = True
                self.ack_thread = threading.Thread(
                    target=self._ack_receiver_loop, daemon=True
                )
                self.transmit_thread = threading.Thread(
                    target=self._retransmitter_loop, daemon=True
                )
                self.transmit_thread.start()
                self.ack_thread.start()

    def send_data(self, segment: Segment, max_retry: int = 10):
        self.wakeup_threads()
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
                        "max_retry":max_retry,
                    }

                    is_op_end = ""
                    if segment.opcode == const.OP_END:
                        is_op_end = " PAQUETE END"
                    logger.debug(f"Envío paquete{is_op_end}: {self.next_seq}")
                    self.socket.sendto(segment.pack(), self.address)
                    self.next_seq += 1
                    return
                self.cond.wait()
        if not self.closing:
                raise ConnectionError("[SR] reintentos de envió agotados")

    def _retransmitter_loop(self):
        """Hilo Emisor: itera buscando paquetes con timer expirado"""
        while self.active:
            now = time.time()
            with self.cond:
                # Usamos list(keys) para poder borrar elementos sin error
                for seq in list(self.window_data.keys()):
                    entry = self.window_data[seq]

                    if entry["state"] == State.IN_FLIGHT:
                        # Si pasó el tiempo de timeout
                        if now - entry["time_stamp"] > self.timeout:
                            if entry["retry"] <= 0:
                                # Si estamos en proceso de cierre o el paquete es el fin, se sale
                                if self.closing:
                                    self.window_data.pop(seq, None)
                                    continue
                                # falló la conexión!
                                self.active = False
                                break
                            if self.closing:
                                self.window_data.pop(seq, None)
                                continue
                            logger.debug(
                                f"Retransmitiendo seq={seq} (quedan {entry['retry']} reintentos)"
                            )
                            self.socket.sendto(entry["seg"].pack(), self.address)
                            entry["time_stamp"] = now
                            entry["retry"] -= 1

                self.cond.wait(timeout=self.timeout)# duermo hasta este evento

    def _ack_receiver_loop(self):
        """Hilo Receptor: ACKs para deslizar la ventana"""
        while self.active:
            try:
                self.socket.settimeout(self.timeout)
                raw_data, _ = self.socket.recvfrom(self.receive_tam)
                ack_pkt = Segment.unpack(raw_data)

                if ack_pkt.opcode != const.OP_ERROR:
                    seq = ack_pkt.seq_num
                    with self.cond:
                        # Si recibo un ack que esta en ventana
                        if seq in self.window_data:
                            entry = self.window_data[seq]
                            if entry["retry"] == entry["max_retry"]:  # no fue retransmitido
                                rtt = time.time() - entry["time_stamp"]
                                self.set_timeout(rtt)
                            self.window_data[seq]["state"] = State.ACKED
                            logger.debug(f"ACK recibido seq={seq}")
                            # Deslizar ventana: eliminamos los paq Acked
                            self._slide_window()
                            #esta condicion despierta a los demas threads
                            self.cond.notify_all()

            except (socket.timeout, ValueError):
                continue
            except Exception:
                continue

    def receive_data(self) -> Tuple[int, Optional[bytes]]:
        """Lógica de recepción con buffer para paquetes fuera de orden"""
        self.socket.settimeout(self.timeout)
        # tiempo del último paq recibido
        last_received = time.time()
        # tiempo maximo esperando cualquier paquete
        max_time_waiting = 2.0 + self.max_recv_retry * self.timeout
        # active se desactiva por stop_strategy() desde el rdtsocket
        # active solo se desactiva forzosamente si falla _retransmitter_loop()
        while self.active:
            time_wating_packets = time.time() - last_received
            if time_wating_packets > max_time_waiting:
                raise ConnectionError("Conexión perdida: el emisor no responde")
            # Se fija si el paquete base ya esta en el buffer
            if self.recv_base_seq in self.recv_buffer:
                # cada vez que voy a entregar algo, reseteo el timer
                last_received = time.time()
                seg = self.recv_buffer.pop(self.recv_base_seq)
                # Deslizamos la ventana
                self.recv_base_seq += 1
                # Entrego el payload
                return (seg.opcode, seg.payload)
            try:
                # Recibir el paquete
                payload, addr = self.socket.recvfrom(self.receive_tam)
                # cada vez que recibo algo, reseteo el timer
                last_received = time.time()
                if addr != self.address:
                    continue
                segment = Segment.unpack(payload)
            except socket.timeout:
                continue
            except Exception as e:
                logger.debug(f"[SR] Paquete no recibido. {e}")
                continue
            seq = segment.seq_num
            # Marco como ack siempre
            self._send_ack(seq)
            self._buff_segment(segment)
            # Caso de error! Entrego directamente
            if segment.opcode == const.OP_ERROR:
                return (const.OP_ERROR, segment.payload)

    def _slide_window(self):
        # Importante usar self.lock sino ff
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
        """Guarda el segmento en el buffer si está dentro de la ventana de recepcion"""
        seq = segment.seq_num
        win_tam = self.recv_base_seq + self.wsize
        # si el seqnumber esta entre la base y el tamaño de ventana
        if self.recv_base_seq <= seq < win_tam:
            if seq not in self.recv_buffer:
                self.recv_buffer[seq] = segment
                logger.debug(f"Buffereado seq={seq}")    
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
