import threading

from server.handler import ClientHandler
from server.registry import ClientRegistry


class ClientDispatcher:
    def __init__(self, sock, storage):
        self.sock = sock
        self.storage = storage
        self.registry = ClientRegistry()

    def dispatch(self, data, addr):
        handler, is_new = self.registry.register_if_new(
            addr,
            lambda: ClientHandler(self.sock, addr, self.storage),
        )

        if is_new:
            thread = threading.Thread(target=handler.handle, args=(data,))
            thread.daemon = True
            thread.start()
        else:
            handler.receive(data)
