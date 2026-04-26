import struct

class Segment:
    HEADER_SIZE = 4

    def __init__(self, seq: int, ack: int, payload: bytes):
        self.seq = seq
        self.ack = ack
        self.payload = payload

    def to_bytes(self) -> bytes:
        header = bytes([self.seq, self.ack]) + b"\x00\x00"
        cksum = self._crc16(header + self.payload)
        return bytes([self.seq, self.ack]) + struct.pack("!H", cksum) + self.payload

    @classmethod
    def from_bytes(cls, data: bytes):
        if len(data) < cls.HEADER_SIZE:
            return None

        seq, ack = data[0], data[1]
        cksum = struct.unpack("!H", data[2:4])[0]
        payload = data[4:]

        header = bytes([seq, ack]) + b"\x00\x00"
        if cls._crc16(header + payload) != cksum:
            return None

        return cls(seq, ack, payload)

    @staticmethod
    def _crc16(data: bytes) -> int:
        crc = 0xFFFF
        for byte in data:
            crc ^= byte << 8
            for _ in range(8):
                crc = (crc << 1) ^ 0x1021 if crc & 0x8000 else crc << 1
                crc &= 0xFFFF
        return crc
