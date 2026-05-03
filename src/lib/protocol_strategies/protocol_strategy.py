from typing import Optional, Tuple
import socket as sckt
import lib.const as const
from lib.segment import Segment
from lib.logger import logger

class ProtocolStrategy:
        
    def __init__(self,address,socket,timeout=const.TIMEOUT):
        self.timeout=timeout
        self.receive_tam=4096 #Esto es más que un paq, por seguridad
        self.base_seq=1
        self.next_seq=1
        
        self.recv_base_seq=1
        self.recv_next_seq=1
        
        
        self.address=address
        self.socket:sckt.socket=socket
        self.wsize=const.SV_MAX_WIN
        self.active=True
        self.closing = False
    def set_window(self,tam:int)->None:
        self.wsize=tam
    def send_data(self, segment:Segment, max_retry:int=10)-> Optional[Segment]:
        pass
    def receive_data(self,max_retry=10) -> Tuple[int, Optional[bytes]]:
        pass
    def stop_strategy(self):
        """Para limpiar hilos y demas cosas en cada estrategia"""
        pass
    def is_finished(self):
        pass
    def set_timeout(self, rtt):
        """Solo se llama en el handshake
        inspirado en RFC 793: Página 40 sobre Retransmission Timeout
        SRTT = ( ALPHA * SRTT ) + ((1-ALPHA) * RTT)

        and based on this, compute the retransmission timeout (RTO) as:

        RTO = min[UBOUND,max[LBOUND,(BETA*SRTT)]]
        """
        lbound = const.TIMEOUT 
        ubound = 10.0   # 1s
        beta = 2
        rto = min(ubound, max(lbound, beta * rtt)) #Retransmission timeout
        # nuevo_timeout = (1-a) * old_timeout + a*rto
        self.timeout = 0.8 * self.timeout + 0.2*rto
        logger.debug(f"RTT: {rtt*1000:.1f}ms → RTO: {rto*1000:.1f}ms")