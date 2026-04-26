import socket
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.lib.model.ftp.segment.const import *
from src.lib.model.ftp.segment.segment import Segment





client_socket=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
dest=('10.0.0.2',65535)
msg=b"TEST de protocolo"
for i in range(1,65535):
    segment=Segment(OP_START_UPLOAD,i,10,msg)
    client_socket.sendto(segment.pack(),dest)
print("Enviado!")
