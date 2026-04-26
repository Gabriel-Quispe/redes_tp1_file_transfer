class SRBuffer:
    def __init__(self, max_seq: int):
        self._buffer = {}
        self._base = 0
        self._max_seq = max_seq

    def add(self, seq: int, payload: bytes):
        if seq not in self._buffer:
            self._buffer[seq] = payload

    def pop_in_order(self):
        if self._base not in self._buffer:
            return None

        data = self._buffer.pop(self._base)
        self._base = (self._base + 1) % self._max_seq

        while self._base in self._buffer:
            data += self._buffer.pop(self._base)
            self._base = (self._base + 1) % self._max_seq

        return data

    @property
    def base(self):
        return self._base
