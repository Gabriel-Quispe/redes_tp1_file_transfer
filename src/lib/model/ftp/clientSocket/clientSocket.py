from socket import *
#import segment

class ClientSocket:

	def __init__(self, host, port, dest_addr):
		self.host = host
		self.port = port
        self.dest.addr = dest_addr
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def connect():
    	self.sock.connect()

    def send(self, data):
        self.sock.sendto(segment, addr)

    def receive(self):
        return self.sock.recvfrom(65535)

    def close(self):
        self.sock.close()

    
"""
serverName = "127.0.0.1"
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_DGRAM)
message = input("Ingrese mensaje: ")
clientSocket.sendto(message.encode(),(serverName, serverPort))
modifiedMessage, serverAddress = clientSocket.recvfrom(2048)
print(modifiedMessage.decode())
clientSocket.close()
""""
