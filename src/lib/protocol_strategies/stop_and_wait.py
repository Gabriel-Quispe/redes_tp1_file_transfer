from typing import Tuple

from .protocol_strategy import *
from lib.segment import *
from lib.logger import logger
import socket
class StopAndWait(ProtocolStrategy):
    def __init__(self, address, socket,timeout):
        super().__init__(address, socket,timeout)
        self.wsize = 1
        self.bit_sw = 1
    def set_window(self,tam:int):
        self.wsize=1
    
    # Por lo general max retry siempre es None, solo se usa en el cierre de la conexión
    # para evitar el problema de los ejercitos
    def send_data(self, segment:Segment, max_retry:Optional[int]=10)-> Optional[Segment]:
        retries = 0
        while retries<max_retry:
            #acá fuerzo que se use este protocolo
            segment.seq_num=self.bit_sw
            
            self.socket.sendto(segment.pack(), self.address)
            try:
                self.socket.settimeout(const.TIMEOUT)
                raw_data, addr = self.socket.recvfrom(self.receive_tam)
                ack_pkt = Segment.unpack(raw_data)

                if ack_pkt.opcode == const.OP_ACK and ack_pkt.seq_num == segment.seq_num:
                    logger.debug(f"ACK recibido para seq {segment.seq_num}")
                    self.bit_sw=1-self.bit_sw
                    return ack_pkt
            #acá el bucle sigue al igual que en el libro    
            except (socket.timeout, ValueError):
                retries+=1
                logger.error(f"TIMEOUT! REINTENTO {retries}")
                if max_retry is not None and retries>=max_retry:
                    raise ConnectionError("Cerrando conexion ")
                logger.debug(f"Retransmitiendo seq {segment.seq_num}...")
                continue
    
    def receive_data(self,max_retry=10) -> Tuple[int, Optional[bytes]]:
        # acá evito que se muera el receptor(cliente y servidor puede ser receptores)
        self.socket.settimeout(const.TIMEOUT)
        retries=0
        while retries<max_retry:
            try:
                raw_data, addr = self.socket.recvfrom(self.receive_tam)
                # por las dudas
                if addr != self.address: continue 
                
                # Acá el checksum es verificado
                segment = Segment.unpack(raw_data)
                
                ack_segment = Segment(const.OP_ACK, segment.seq_num, self.wsize, b"")
                self.socket.sendto(ack_segment.pack(), self.address)
                if segment.opcode == const.OP_END:
                    logger.info("Fin de transmisión recibido.")                    
                    return (const.OP_END,None)
                if segment.opcode == const.OP_ERROR:
                    return (const.OP_ERROR,segment.payload)
                if segment.seq_num == self.bit_sw:               
                    self.bit_sw = 1- self.bit_sw
                    if segment.opcode == const.OP_DATA:
                        return (const.OP_DATA,segment.payload)
                    logger.debug(f"Paquete de operacion {segment.opcode}")
                    continue
                else:
                    logger.debug(f"Seq {segment.seq_num} DUPLICADO.")
            except Exception as e:
                # En snw se espera el timeout 
                logger.debug(f"Error {e}")
                retries+=1
                continue