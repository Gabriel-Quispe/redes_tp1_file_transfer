import threading


class ClientRegistry:
    def __init__(self):
        self.clients = {}
        self.lock = threading.Lock()

    def register_if_new(self, addr, handler_factory):
        with self.lock:
            if addr not in self.clients:
                handler = handler_factory()
                self.clients[addr] = handler
                return handler, True
            return self.clients[addr], False

    def get(self, addr):
        with self.lock:
            return self.clients[addr]
