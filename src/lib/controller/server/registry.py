import threading as th


class ClientRegistry:
    def __init__(self):
        self._clients = {}
        self._lock = th.Lock()

    def register_if_new(self, addr, factory):
        with self._lock:
            if addr not in self._clients:
                client = factory()
                self._clients[addr] = client
                return client, True
            return self._clients[addr], False

    def get(self, addr):
        with self._lock:
            return self._clients[addr]
