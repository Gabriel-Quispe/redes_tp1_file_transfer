from typing import Optional
import socket as sckt
import lib.const as const
from lib.segment import Segment
class ProtocolStrategy:
    def __init__(self,address,socket):
        self.receive_tam=4096 #Esto es más que un paq, por seguridad
        self.next_seq=1
        self.address=address
        self.socket:sckt.socket=socket
        self.wsize=const.SV_MAX_WIN
    def set_window(self,tam:int)->None:
        pass
    def send_data(self,payload)-> Optional[Segment]:
        pass
    def do_handshake(self,segment: Segment)-> Optional[Segment]:
        return self.send_data(segment)
    def receive_data(self)-> Optional[bytes]:
        pass