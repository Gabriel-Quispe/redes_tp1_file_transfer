import threading as th
from server.handler import ClientHandler


class ClientDispatcher:
    def __init__(self, sock, store, reg):
        self.sock = sock
        self.store = store
        self.reg = reg

    def dispatch(self, data, addr):
        handler, is_new = self.reg.register_if_new(addr,
        lambda: ClientHandler(self.sock, addr, self.store))

        if is_new:
            thread = th.Thread(
                target=handler.handle,
                args=(data,)
            )
            thread.daemon = True
            thread.start()
        else:
            handler.receive(data)
