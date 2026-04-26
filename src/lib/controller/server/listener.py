class ServerListener:
    def __init__(self, sk, dispatcher) -> None:
        self._sk = sk
        self._dispatcher = dispatcher
        self._running = False

    def start(self) -> None:
        self._running = True
        while self._running:
            try:
                data, addr = self._sk.receive()
                self._dispatcher.dispatch(data, addr)
            except OSError:
                break

    def stop(self) -> None:
        self._running = False
