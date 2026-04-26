from model.rdt.stop_and_wait.segment import Segment


class UDPBase:
    def __init__(self, sock, addr, inbox=None):
        self._sock = sock
        self._addr = addr
        self._inbox = inbox

    def send_segment(self, segment: Segment):
        self._sock.sendto(segment.to_bytes(), self._addr)

    def receive_segment(self):
        data, addr = self._recv_raw()
        seg = Segment.from_bytes(data)
        return seg, addr

    def _recv_raw(self):
        if self._inbox:
            return self._inbox.get()
        return self._sock.recvfrom(65535)