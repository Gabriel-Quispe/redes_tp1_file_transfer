import struct
import socket
import lib.const as const
from lib.segment import Segment
from lib.protocol_strategies.selective_repeat import *
from lib.protocol_strategies.stop_and_wait import *
from lib.protocol_strategies.protocol_strategy import *
from lib.logger import logger
# recibe una direccion y una strategy (Stop n Wait o Selective Repeat)
class FRDTSocket:
    def __init__(self,address,protocol_strategy):
        self.next_seq = 1
        self.protocol_id = protocol_strategy
        self.address = address
        self.socket:socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.wsize=const.SV_MAX_WIN
        self.p_strategy:ProtocolStrategy=None
        match protocol_strategy:
            case const.PROTOCOL_SR:
                self.p_strategy = SelectiveRepeat(self.address,self.socket)
            case const.PROTOCOL_SW:
                self.p_strategy = StopAndWait(self.address,self.socket)
            case _:
                raise ValueError("Protocolo no soportado!")
        logger.debug(f"Iniciando socket para {self.address} con protocolo {self.p_strategy.__class__}")
    #hanshake
    def connect(self,op_start, file_name=None, size=0):
        # lado del cliente
        if file_name is not None:
            logger.debug(f"Intenando subir {file_name} de {size} bytes ")
            data_payload = struct.pack("!BQ", self.protocol_id, size) + file_name.encode()
            # segment inicial con:
            # operacion de inicio
            # seqnumber en 0
            # tamaño de ventana maxima! (la propone el cliente)
            # informacion sobre el protocolo y el archivo en el payload
            request_segment = Segment(op_start,0,self.wsize,data_payload)
            # el request lo envia la strategy (porque se puede perder)
            server_response_segment: Segment=self.p_strategy.do_handshake(request_segment)
            if not server_response_segment:
                logger.error("El servidor no respondio al handshake")
                raise ConnectionError("Error de conexion!")
            self.wsize = server_response_segment.wsize
            self.p_strategy.set_window(self.wsize)
            logger.info(f"Conexion establecida!, ventana receptora {self.wsize}")
            return server_response_segment
        else:#somos el servidor
            logger.debug("Servidor esperando paquete inicial...")
            raw_data, addr = self.socket.recvfrom(const.MAX_PAYLOAD_SIZE)
            
            self.address = addr
            self.p_strategy.address = addr 
            client_request = Segment.unpack(raw_data)
            logger.debug(f"Pedido recibido de {addr}. Enviando confirmacion...")
            self.wsize = const.SV_MAX_WIN // const.SV_MAX_CLIENTS
            response_segment = Segment(const.OP_ACK, 0, self.wsize, b"")            
            self.socket.sendto(response_segment.pack(), self.address)
            
            self.p_strategy.set_window(self.wsize)            
            return client_request
    
    def send(self,data):
        size = const.MAX_PAYLOAD_SIZE
        
        for i in range(0, len(data), size):
            payload=data[i:i + size]
            segment = Segment(const.OP_DATA, self.next_seq, self.wsize, payload)
            logger.debug(f"Enviando DATA con seq={self.next_seq}")
            
            # La estrategia se encarga de que este segmento llegue
            self.p_strategy.send_data(segment)
            
            self.next_seq += 1
    def recv(self):
        logger.debug(f"Recibiendo DATA")
        payload = self.p_strategy.receive_data()
        return payload
    
    def close(self):
        logger.info(f"cerrando conexion")
        finack = Segment(const.OP_END, self.next_seq, 0, b"")
        self.p_strategy.do_handshake(finack) # es un handshake de fin
        self.socket.close()