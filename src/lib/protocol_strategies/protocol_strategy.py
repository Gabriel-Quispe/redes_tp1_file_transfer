from typing import Optional, Tuple
import socket as sckt
import lib.const as const
from lib.segment import Segment
from lib.logger import logger
class ProtocolStrategy:
    def __init__(self,address,socket):
        self.receive_tam=4096 #Esto es más que un paq, por seguridad
        self.next_seq=1
        self.address=address
        self.socket:sckt.socket=socket
        self.wsize=const.SV_MAX_WIN
    def set_window(self,tam:int)->None:
        pass
    def send_data(self, segment:Segment, max_retry:Optional[int]=None)-> Optional[Segment]:
        pass
    def do_handshake(self,segment: Segment)-> Optional[Segment]:        
        
        while True:
            # intentamos enviar el paquete de inicio
            # hasta que alguien responda
            self.socket.sendto(segment.pack(), self.address)            
            try:
                self.socket.settimeout(const.TIMEOUT)
                raw_data, hilo_address = self.socket.recvfrom(self.receive_tam)
                recv_response = Segment.unpack(raw_data)
                
                #si el receptor respondio al handshake!
                if recv_response.opcode == const.OP_ACK:
                    # actualizamos el nuevo address (provisto por el server)
                    self.address = hilo_address
                    return recv_response                
                if recv_response.opcode == const.OP_ERROR:
                    logger.error(f"Error en handshake! {recv_response.payload}")
                    raise ConnectionAbortedError(recv_response.payload.decode())
            except (sckt.timeout, ValueError):
                continue
    def receive_data(self) -> Tuple[int, Optional[bytes]]:
        pass