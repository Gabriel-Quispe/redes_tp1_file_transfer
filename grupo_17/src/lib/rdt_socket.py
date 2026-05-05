import time
import socket
import lib.const as const
from lib.segment import Segment
from lib.protocol_strategies.selective_repeat import SelectiveRepeat
from lib.protocol_strategies.stop_and_wait import StopAndWait
from lib.protocol_strategies.protocol_strategy import ProtocolStrategy
from lib.logger import logger
from typing import Tuple, Optional

# recibe una direccion y una strategy (Stop n Wait o Selective Repeat)


class Role:
    Sender = 1
    Receiver = 2


TIMEOUT = const.TIMEOUT


class FRDTSocket:
    def __init__(self, address, strategy, timeout=TIMEOUT, max_win=None):
        self.role: Role = None
        self.timeout = timeout
        self.max_win = max_win
        # self.next_seq = 1
        self.protocol_id = strategy
        self.address = address
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.wsize = const.SV_MAX_WIN
        self.p_strategy: ProtocolStrategy = None
        protocol_name = ""
        match strategy:
            case const.PROTOCOL_SR:
                self.p_strategy = SelectiveRepeat(self.address, self.socket)
                protocol_name = "Selective Repeat"
            case const.PROTOCOL_SW:
                sw = StopAndWait(self.address, self.socket, self.timeout)
                self.p_strategy = sw
                protocol_name = "Stop n Wait"
            case _:
                raise ValueError("Protocolo no soportado!")
        logger.debug(f"Iniciando {self.address} con protocolo {protocol_name}")

    def connect(self, op_start, payload=b"") -> Segment:
        """Inicio de conexión. esta llamada viene del lado del cliente.
        La capa superior (Applayer) usa este metodo para iniciar la conexion
        """
        if self.role is None:
            raise RuntimeError("Se debe setear un rol")
        logger.debug(f"Iniciando conexión con opcode {op_start}")
        # la capa de transporte mete el payload en un segmento
        request_segment = Segment(op_start, 0, self.wsize, payload)

        # El socket se encarga del handshake
        response_segment = self._do_handshake(request_segment)
        # luego del handshake, debe retornar
        # la nueva direccion dada por el server
        self.address = self.p_strategy.address

        # flujo de errores
        if not response_segment:
            logger.error("El servidor no respondió al handshake del cliente")
            raise ConnectionError("Error: Timeout en handshake")
        # Actualizamos ventana según lo que el servidor nos permitió
        self.wsize = response_segment.wsize
        self.p_strategy.set_window(self.wsize)

        logger.info(f"Conexión establecida. Ventana: {self.wsize}")
        return response_segment

    def accept_connection(self, opcode, payload: bytes = b"") -> Segment:
        """Acepta la conexion, negociando tamaño de ventana"""
        self.wsize = (
            const.SV_MAX_WIN // const.SV_MAX_CLIENTS
            if self.max_win is None
            else self.max_win
        )
        response_segment = Segment(opcode, 0, self.wsize, payload)
        logger.debug(f"Enviando respuesta inicial {opcode} a {self.address}")
        self.socket.sendto(response_segment.pack(), self.address)
        if opcode == const.OP_ACK:
            self.p_strategy.set_window(self.wsize)
        return response_segment

    def send(self, data):
        """La capa superior (AppLayer) usa este método para enviar archivos"""
        size = const.MAX_PAYLOAD_SIZE
        for i in range(0, len(data), size):
            pos = i + size
            payload = data[i:pos]
            segment = Segment(const.OP_DATA, 0, self.wsize, payload)
            logger.debug(f"Enviando DATA con seq={self.p_strategy.next_seq}")
            # La estrategia se encarga de que este segmento llegue
            self.p_strategy.send_data(segment)

    def send_error(self, message: str):
        """Notifica un error. Se llama desde una capa superior, y
        se realizan intentos Best Effort"""
        error_segment = Segment(const.OP_ERROR, 0, 1, message.encode())
        # 3 intentos cada 20ms
        for _ in range(3):
            try:
                self.socket.sendto(error_segment.pack(), self.address)
                time.sleep(self.timeout * 2)
            except Exception:
                pass

    def recv(self) -> Tuple[int, Optional[bytes]]:
        """Acá se reciben todo tipo de paquetes. Se levanta un error con
        los paquetes OP_ERROR
        """
        logger.debug("Recibiendo paquete")
        op, payload = self.p_strategy.receive_data()
        if op == const.OP_ERROR:
            err = payload.decode() if payload else ""
            logger.error(f"Error transmitiendo datos: {err}")
            self.close()
            raise ConnectionError(
                f"Error remoto: {payload.decode() if payload else ''}"
            )
        return op, payload

    def close(self):
        if not self.p_strategy.active and self.p_strategy.closing:
            return
        if self.role == Role.Sender:
            # espero que se vacié la ventana de envio
            while self.p_strategy.base_seq != self.p_strategy.next_seq:
                if not self.p_strategy.active:
                    return
                time.sleep(0.01)
        logger.info("[Socket] Cerrando conexión...")
        fin_segment = Segment(const.OP_END, self.p_strategy.next_seq, 1, b"")
        # Best Effort se manda el END varias veces
        if self.role == Role.Sender:
            best_effort_teardown = self.timeout / 2
            for _ in range(3):
                try:
                    self.socket.sendto(fin_segment.pack(), self.address)
                except Exception:
                    pass  # estamos cerrando, no hace falta elevar errores
                time.sleep(best_effort_teardown)
        else:
            # Si soy el Receptor de los datos, espero un poco
            time.sleep(self.timeout * 2)
        self.p_strategy.stop_strategy()
        self.socket.close()
        logger.info("Socket liberado")

    def set_role(self, role: Role):
        self.role = role

    def _do_handshake(self, segment: Segment) -> Optional[Segment]:
        max_try = 50
        while max_try > 0:
            # intentamos enviar el paquete de inicio
            # hasta que alguien responda
            self.socket.sendto(segment.pack(), self.address)
            try:
                self.socket.settimeout(self.timeout * 2)
                raw_data, hilo_address = self.socket.recvfrom(1024)
                recv_response = Segment.unpack(raw_data)

                # si el receptor respondio al handshake!
                if recv_response.opcode == const.OP_ACK:
                    # actualizamos el nuevo address (provisto por el server)
                    self.address = hilo_address
                    self.p_strategy.address = hilo_address
                    return recv_response
                if recv_response.opcode == const.OP_ERROR:
                    err_msg = recv_response.payload
                    logger.error(f"Error en handshake! {err_msg}")
                    raise ConnectionAbortedError(err_msg.decode())
            except (socket.timeout, ValueError):
                max_try -= 1
                continue
