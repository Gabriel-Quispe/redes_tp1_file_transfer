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
    def __init__(self,address,protocol_strategy,timeout=const.TIMEOUT):
        self.timeout=timeout
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
                self.p_strategy = StopAndWait(self.address,self.socket,self.timeout)
            case _:
                raise ValueError("Protocolo no soportado!")
        #actualizo la ventana segun protocolo
        self.wsize = self.p_strategy.wsize
        logger.debug(f"Iniciando socket para {self.address} con protocolo {self.p_strategy.__class__}")
    
    # este handshake viene del lado del cliente.
    # la app inicia la conexion enviando un payload con info ya preparado
    # debe reintentar hasta poder conectarse.
    def connect(self, op_start, payload=b"") -> Segment:
        logger.debug(f"Iniciando conexión con opcode {op_start}")
        # la capa de transporte mete el payload en un segmento
        request_segment = Segment(op_start, 0, self.wsize, payload)
        
        # El socket se encarga del handshake
        response_segment = self.do_handshake(request_segment)
        # luego del handshake, debe retornar la nueva direccion dada por el server
        self.address=self.p_strategy.address
        
        #flujo de errores
        if not response_segment:
            logger.error("El servidor no respondió al handshake del cliente")
            raise ConnectionError("Error: Timeout en handshake")                    
        # Actualizamos ventana según lo que el servidor nos permitió
        self.p_strategy.set_window(response_segment.wsize)
        self.wsize = self.p_strategy.wsize
        
        logger.info(f"Conexión establecida. Ventana del servidor: {self.wsize}")
        return response_segment
    
    
    # este metodo se utiliza para finalizar el handshake inicial.
    # intentara conectarse al servidor varias veces, el servidor sin embargo, no necesita reintentar nada
    
    def accept_connection(self, opcode, payload:bytes=b"")->Segment:
        self.wsize = const.SV_MAX_WIN // const.SV_MAX_CLIENTS        
        # 
        response_segment = Segment(opcode, 0, self.wsize, payload)
        logger.debug(f"Enviando respuesta inicial {opcode} a {self.address}")
        self.socket.sendto(response_segment.pack(), self.address)
        if opcode==const.OP_ACK:
            self.p_strategy.set_window(self.wsize)
        return response_segment
    
    
    def send(self,data):
        size = const.MAX_PAYLOAD_SIZE
        
        for i in range(0, len(data), size):
            payload=data[i:i + size]
            segment = Segment(const.OP_DATA, self.next_seq, self.wsize, payload)
            logger.debug(f"Enviando DATA con seq={self.p_strategy.next_seq}")
            
            # La estrategia se encarga de que este segmento llegue
            self.p_strategy.send_data(segment)
            
            self.next_seq += 1
    def recv(self)->Tuple[int, Optional[bytes]]:
        logger.debug(f"Recibiendo paquete")         
        max_overall_retry = 10
        while max_overall_retry>0:
            try:
                op,payload= self.p_strategy.receive_data()
                if op == const.OP_ERROR:
                    logger.error(f"Error transmitiendo datos: {payload.decode() if payload else "Error"}")
                    max_overall_retry-=1    
                return op, payload
            except socket.timeout:
                max_overall_retry-=1
                continue
        raise ConnectionError("Conexión perdida: El servidor no responde.")
    

    def close(self):
        logger.info(f"cerrando conexion")
        fin_segment = Segment(const.OP_END, self.p_strategy.next_seq, 1, b"")
        # No necesito que sea confiable el close! (se quedan infinitamente esperando el ack del ack
        # como dijeron en clase con el ejemplo de los generales)
        self.socket.settimeout(self.timeout)
        try:
            self.p_strategy.send_data(fin_segment,3)
        except Exception as e:
            logger.info("Cliente cerró su conexion")
        finally:
            self.socket.close()
            logger.info("Server cerró su conexión")
            
    def do_handshake(self,segment: Segment)-> Optional[Segment]:
        max_try=10
        while max_try>0:
            # intentamos enviar el paquete de inicio
            # hasta que alguien responda
            self.socket.sendto(segment.pack(), self.address)
            try:
                self.socket.settimeout(self.timeout*2)
                raw_data, hilo_address = self.socket.recvfrom(1024)
                recv_response = Segment.unpack(raw_data)
                
                #si el receptor respondio al handshake!
                if recv_response.opcode == const.OP_ACK:
                    # actualizamos el nuevo address (provisto por el server)
                    self.address = hilo_address
                    self.p_strategy.address = hilo_address
                    self.wsize=self.p_strategy.wsize
                    return recv_response         
                if recv_response.opcode == const.OP_ERROR:
                    logger.error(f"Error en handshake! {recv_response.payload}")
                    raise ConnectionAbortedError(recv_response.payload.decode())
            except (sckt.timeout, ValueError):
                max_try-=1
                continue