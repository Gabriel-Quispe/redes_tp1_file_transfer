import socket


class ServerSocket:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))

    def receive(self):
        return self.sock.recvfrom(65535)

    def close(self):
        self.sock.close()

    def send(self, data, addr):
        self.sock.sendto(data, addr)

    def sendto(self, data, addr):
        self.sock.sendto(data, addr)
