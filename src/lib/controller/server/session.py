from model.app.router import AppRouter
from model.rdt.router import RDTRouter


class SessionDispatcher:
    def __init__(self, rdt: RDTRouter, store: str) -> None:
        self._rdt = rdt
        self._store = store

    def run(self) -> None:
        try:
            data = self._rdt.recibir_mensaje()
        except RuntimeError:
            return
        AppRouter(self._rdt, self._store).resolver(data)
