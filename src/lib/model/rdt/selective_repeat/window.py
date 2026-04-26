class SRWindow:
    def __init__(self, size: int, max_seq: int):
        self._size = size
        self._max_seq = max_seq
        self._base = 0

    def in_window(self, seq: int) -> bool:
        return (seq - self._base) % self._max_seq < self._size

    def slide(self, acked: set[int]):
        while self._base in acked:
            acked.discard(self._base)
            self._base = (self._base + 1) % self._max_seq

    @property
    def base(self):
        return self._base
