import time


class SRTimerManager:
    def __init__(self, timeout: float):
        self._timeout = timeout
        self._timers = {}

    def start(self, seq: int):
        self._timers[seq] = time.time()

    def ack(self, seq: int):
        self._timers.pop(seq, None)

    def expired(self):
        now = time.time()
        return [seq for seq, t in self._timers.items() if now - t > self._timeout]
