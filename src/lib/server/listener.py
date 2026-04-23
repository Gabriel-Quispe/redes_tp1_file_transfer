class ServerListener:
    def __init__(self, sk, dispath):
        self.sk = sk
        self.dispath = dispath
        self.running = False

    def start(self):
        self.running = True
        while self.running:
            try:
                data, addr = self.sk.receive()
                self.dispath.dispatch(data, addr)
            except OSError:
                break

    def stop(self):
        self.running = False
