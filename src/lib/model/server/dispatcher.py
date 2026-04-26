import threading

from server.registry import ClientRegistry
from server.handler import ClientHandler


class ClientDispatcher:
    def __init__(self, sock, storage):
        self.sock = sock
        self.storage = storage
        self.registry = ClientRegistry()

    def dispatch(self, data, addr):
        if self.registry.is_new(addr):
            handler = ClientHandler(self.sock, addr, self.storage)
            self.registry.register(addr, handler)
            thread = threading.Thread(target=handler.handle, args=(data,))
            thread.daemon = True
            thread.start()
        else:
            self.registry.get(addr).receive(data)
