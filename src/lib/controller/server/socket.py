import socket as s


class ServerSocket:
    SIZE_MAX_BUFFER = 65535

    def __init__(self, host: str, port: int) -> None:
        self.sk = s.socket(s.AF_INET, s.SOCK_DGRAM)
        self.sk.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)
        self.sk.bind((host, port))

    def receive(self) -> tuple[bytes, tuple]:
        return self.sk.recvfrom(self.SIZE_MAX_BUFFER)

    def sendto(self, data: bytes, addr: tuple) -> None:
        self.sk.sendto(data, addr)

    def close(self) -> None:
        self.sk.close()
