import socket as s


class ServerSocket:
    SIZE_MAX_BUFFER = 65535

    def __init__(self, host: str, port: str) -> None:
        self.sk = s.socket(s.AF_INET, s.SOCK_DGRAM)
        self.sk.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)
        self.sk.bind((host, port))

    def receive(self):
        size = self.SIZE_MAX_BUFFER
        return self.sk.recvfrom(size)

    def sendto(self, data, addr):
        self.sk.sendto(data, addr)

    def close(self):
        self.sk.close()
