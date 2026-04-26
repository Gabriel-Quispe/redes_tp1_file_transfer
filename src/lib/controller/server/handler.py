import queue
import threading as th

from model.rdt.router import RDTRouter
from controller.server.session import SessionDispatcher


class ClientHandler:
    def __init__(self, sk, addr, store: str) -> None:
        self.addr   = addr
        self._inbox = queue.Queue()
        self._rdt   = RDTRouter(sk, addr, inbox=self._inbox)
        self._store = store

    def handle(self, data: bytes) -> None:
        self._inbox.put((data, self.addr))
        th.Thread(target=self._run_session, daemon=True).start()

    def receive(self, data: bytes) -> None:
        self._inbox.put((data, self.addr))

    def _run_session(self) -> None:
        SessionDispatcher(self._rdt, self._store).run()
