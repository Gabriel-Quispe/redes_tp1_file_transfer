import queue

from model.rdt.stop_and_wait.segment import Segment

TIMEOUT = 0.5


class UDPBase:
    def __init__(self, sock, addr, inbox=None):
        self._sock = sock
        self._addr = addr
        self._inbox = inbox
        if self._inbox is None:
            self._sock.settimeout(TIMEOUT)

    def send_segment(self, segment: Segment):
        self._sendto(segment.to_bytes(), self._addr)

    def receive_segment(self):
        data, addr = self._recv_raw()
        seg = Segment.from_bytes(data)
        return seg, addr

    def _sendto(self, data: bytes, addr: tuple) -> None:
        self._sock.sendto(data, addr)

    def _recv_raw(self):
        if self._inbox:
            try:
                return self._inbox.get(timeout=TIMEOUT)
            except queue.Empty as e:
                raise TimeoutError from e
        return self._sock.recvfrom(65535)
