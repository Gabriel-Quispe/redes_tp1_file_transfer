import socket
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.lib.model.ftp.segment.segment import Segment

server_socket= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('',65535))

while True:
    data,address = server_socket.recvfrom(2000)
    try:
        segment=Segment.unpack(data)
        print(f"Llego paquete con codigo de operacion: {segment.opcode}")
        print(f"Codigo se secuencia: {segment.seq_num}")
        print(f"Data: {segment.payload.decode()}")
    except Exception as e:
        print(f"Error!: {e}")