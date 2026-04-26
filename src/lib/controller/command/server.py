<<<<<<< HEAD
import threading as th

from view.cli.server import ServerCLI
from view.params.server import ServerParams
from controller.server.dispatcher import ClientDispatcher
from controller.server.listener import ServerListener
from controller.server.registry import ClientRegistry
from controller.server.socket import ServerSocket


class ServerCommand:
    def execute(self) -> None:
        args = ServerCLI().args()
        params = ServerParams(args)

        sk = ServerSocket(params.host, params.port)
        reg = ClientRegistry()
        dispatcher = ClientDispatcher(sk, params.storage, reg)
        listener = ServerListener(sk, dispatcher)

        thread = th.Thread(target=listener.start, daemon=True)
=======
import threading

from cli.server import ServerCLI
from params.server import ServerParams
from server.socket import ServerSocket
from server.dispatcher import ClientDispatcher
from server.listener import ServerListener


class ServerCommand:
    def execute(self):
        args = ServerCLI().args()
        params = ServerParams(args)

        server_socket = ServerSocket(params.host, params.port)
        dispatcher = ClientDispatcher(server_socket, params.storage)
        listener = ServerListener(server_socket, dispatcher)

        thread = threading.Thread(target=listener.start)
        thread.daemon = True
>>>>>>> main
        thread.start()

        while input() != "exit":
            pass

        print("Shutting down server...")
        listener.stop()
<<<<<<< HEAD
        sk.close()
=======
        server_socket.close()
>>>>>>> main
