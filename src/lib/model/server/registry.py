import threading


class ClientRegistry:
    def __init__(self):
        self.clients = {}
        self.lock = threading.Lock()

    def is_new(self, addr):
        with self.lock:
            return addr not in self.clients

    def register(self, addr, handler):
        with self.lock:
            self.clients[addr] = handler

    def get(self, addr):
        with self.lock:
            return self.clients[addr]
