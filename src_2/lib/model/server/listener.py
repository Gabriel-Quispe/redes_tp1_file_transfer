class ServerListener:
    def __init__(self, server_socket, dispatcher):
        self.server_socket = server_socket
        self.dispatcher = dispatcher
        self.running = False

    def start(self):
        self.running = True
        while self.running:
            try:
                data, addr = self.server_socket.receive()
                self.dispatcher.dispatch(data, addr)
            except OSError:
                break

    def stop(self):
        self.running = False
