from .protocol_strategy import *
from lib.segment import *
from lib.logger import logger
import socket
class StopAndWait(ProtocolStrategy):
    def __init__(self, address, socket):
        super().__init__(address, socket)
        # ignoro el seqnumber, uso 0 y 1!
        self.bit_sw = 1
    def set_window(self,tam:int):
        self.wsize = tam
    
    def send_data(self, segment:Segment)-> Optional[Segment]:
        while True:
            #acá fuerzo que se use este protocolo
            segment.seq_num=self.bit_sw
            
            self.socket.sendto(segment.pack(), self.address)
            try:
                self.socket.settimeout(const.TIMEOUT)
                raw_data, addr = self.socket.recvfrom(const.MAX_PAYLOAD_SIZE)
                ack_pkt = Segment.unpack(raw_data)

                if ack_pkt.opcode == const.OP_ACK and ack_pkt.seq_num == segment.seq_num:
                    logger.debug(f"ACK recibido para seq {segment.seq_num}")
                    self.bit_sw=1-self.bit_sw
                    return ack_pkt
            #acá el bucle sigue al igual que en el libro    
            except (socket.timeout, ValueError):
                logger.debug(f"Retransmitiendo seq {segment.seq_num}...")
                continue
    
    def receive_data(self)-> Optional[bytes]:
        # acá evito que se muera el receptor(cliente y servidor puede ser receptores)
        self.socket.settimeout(None)
        while True:
            try:
                raw_data, addr = self.socket.recvfrom(const.MAX_PAYLOAD_SIZE)
                # por las dudas
                if addr != self.address: continue 
                
                # Acá el checksum es verificado
                segment = Segment.unpack(raw_data)
                
                ack_segment = Segment(const.OP_ACK, segment.seq_num, self.wsize, b"")
                self.socket.sendto(ack_segment.pack(), self.address)
                if segment.opcode == const.OP_END:
                    logger.info("Fin de transmisión recibido.")
                    return None 
                
                if segment.seq_num == self.bit_sw:               
                    self.bit_sw = 1- self.bit_sw
                    return segment.payload
                else:
                    logger.debug(f"Seq {segment.seq_num} DUPLICADO.")

            except ValueError:
                # En snw se espera el timeout 
                logger.debug("Segmento CORRUPTO")
                continue