import threading as th


class ClientRegistry:
    def __init__(self):
        self.clients = {}
        self.lock = th.Lock()

    def register_if_new(self, addr, new_client):
        with self.lock:
            if addr not in self.clients:
                client = new_client()
                self.clients[addr] = client
                return client, True
            return self.clients[addr], False

    def get(self, addr):
        with self.lock:
            return self.clients[addr]
