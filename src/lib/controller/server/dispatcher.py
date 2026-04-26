from controller.server.handler import ClientHandler


class ClientDispatcher:
    def __init__(self, sock, store: str, registry) -> None:
        self._sock = sock
        self._store = store
        self._registry = registry

    def dispatch(self, data: bytes, addr: tuple) -> None:
        handler, is_new = self._registry.register_if_new(
            addr, lambda: ClientHandler(self._sock, addr, self._store)
        )
        if is_new:
            handler.handle(data)
        else:
            handler.receive(data)
