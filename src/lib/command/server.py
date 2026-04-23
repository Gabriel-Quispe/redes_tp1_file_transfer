import threading

from cli.server import ServerCLI
from params.server import ServerParams
from server.dispatcher import ClientDispatcher
from server.listener import ServerListener
from server.socket import ServerSocket
from server.registry import ClientRegistry



class ServerCommand:
    def execute(self):
        args = ServerCLI().args()
        params = ServerParams(args)

        server_socket = ServerSocket(params.host, params.port)
        registry = ClientRegistry()
        dispatcher = ClientDispatcher(server_socket, params.storage, registry)
        listener = ServerListener(server_socket, dispatcher)

        thread = threading.Thread(target=listener.start)
        thread.daemon = True
        thread.start()

        while input() != "exit":
            pass

        print("Shutting down server...")
        listener.stop()
        server_socket.close()
