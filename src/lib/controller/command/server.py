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
        thread.start()

        while input() != "exit":
            pass

        print("Shutting down server...")
        listener.stop()
        sk.close()
