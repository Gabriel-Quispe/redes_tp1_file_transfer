import threading

from cli.server import ServerCLI
from params.server import ServerParams
from server.dispatcher import ClientDispatcher
from server.listener import ServerListener
from server.socket import ServerSocket


class ServerCommand:
    def execute(self):
        args = ServerCLI().args()
        params = ServerParams(args)

        server_socket = ServerSocket(params.host, params.port)
        dispatcher = ClientDispatcher(server_socket, params.storage)
        listener = ServerListener(server_socket, dispatcher)

        thread = threading.Thread(target=listener.start)
        thread.daemon = True
        thread.start()

        while input() != "exit":
            pass

        print("Shutting down server...")
        listener.stop()
        server_socket.close()
