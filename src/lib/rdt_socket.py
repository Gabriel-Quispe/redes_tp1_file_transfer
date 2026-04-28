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
        
        # la estrategia elegida se encarga de asegurar el handshake,
        # devolviendo el segmento de respuesta del server
        response_segment = self.p_strategy.do_handshake(request_segment)
        # luego del handshake, debe retornar la nueva direccion dada por el server
        self.address=self.p_strategy.address
        
        #flujo de errores
        if not response_segment:
            logger.error("El servidor no respondió al handshake del cliente")
            raise ConnectionError("Error: Timeout en handshake")                    
        # Actualizamos ventana según lo que el servidor nos permitió
        self.wsize = response_segment.wsize
        self.p_strategy.set_window(self.wsize)        
        logger.info(f"Conexión establecida. Ventana del servidor: {self.wsize}")
        return response_segment
    
    
    # este metodo se utiliza para finalizar el handshake inicial, dado que el cliente usa un rdt, 
    # intentara conectarse al servidor hasta lograrlo, el servidor sin embargo, no necesita reintentar nada
    # todavia
    # accept_connection no lee nada de ningun socket, se asume que el server lo leyo
    def accept_connection(self, initial_segment):
        self.wsize = const.SV_MAX_WIN // const.SV_MAX_CLIENTS        
        #respuesta ack al start
        response_segment = Segment(const.OP_ACK, 0, self.wsize, b"")        
        logger.debug(f"Enviando ACK inicial a {self.address} de un nuevo puerto")
        self.socket.sendto(response_segment.pack(), self.address)
        self.p_strategy.set_window(self.wsize)        
        return initial_segment
    
    
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
        return self.p_strategy.receive_data()
    

    def close(self):
        logger.info(f"cerrando conexion")
        fin_segment = Segment(const.OP_END, self.p_strategy.next_seq, 1, b"")
        # No necesito que sea confiable el close! (se quedan infinitamente esperando el ack del ack
        # como dijeron en clase con el ejemplo de los generales)
        self.socket.settimeout(const.TIMEOUT)
        try:
            self.p_strategy.send_data(fin_segment,3)
        except Exception as e:
            logger.info("Cliente cerró su conexion")
        finally:
            self.socket.close()
            logger.info("Server cerró su conexión")