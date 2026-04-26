class ClientHandler:
    def __init__(self, sock, addr, storage):
        self.sock = sock  # socket UDP compartido del servidor
        self.addr = addr  # direccion del cliente (ip, puerto)
        self.storage = storage  # carpeta de almacenamiento

    def handle(self, data):
        """
        Punto de entrada del hilo. Recibe el primer mensaje del cliente
        y delega al transfer correspondiente (upload o download).
        """
        pass

    def receive(self, data):
        """
        Recibe mensajes siguientes del mismo cliente durante la transferencia.
        Delega al transfer activo.
        """
        pass
