import queue
import socket
import struct

from app.rdt.rdt import RDTProtocol

TIMEOUT = 0.5
MAX_REINTENTOS = 10
BUFFER_SIZE = 65535
HEADER_SIZE = 4  # SEQ(1) + ACK(1) + CKSUM(2)

SEQ_DATA = 0xFF
SEQ_ACK = 0x00


def _crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


def _build_segment(seq: int, ack: int, payload: bytes) -> bytes:
    header_sin_cksum = bytes([seq, ack]) + b"\x00\x00"
    cksum = _crc16(header_sin_cksum + payload)
    header = bytes([seq, ack]) + struct.pack("!H", cksum)
    return header + payload


def _parse_segment(data: bytes) -> tuple[int, int, bytes] | None:
    if len(data) < HEADER_SIZE:
        return None
    seq, ack = data[0], data[1]
    cksum_recibido = struct.unpack("!H", data[2:4])[0]
    payload = data[HEADER_SIZE:]
    header_sin_cksum = bytes([seq, ack]) + b"\x00\x00"
    cksum_esperado = _crc16(header_sin_cksum + payload)
    if cksum_recibido != cksum_esperado:
        return None
    return seq, ack, payload


class StopAndWait(RDTProtocol):
    """
    Stop & Wait sobre UDP. Sin fragmentación — la capa de aplicación
    es responsable de no superar MAX_SEGMENT_PAYLOAD bytes por mensaje.
    """

    def __init__(
        self,
        sock: socket.socket,
        addr: tuple[str, int],
        inbox: queue.Queue = None,
    ) -> None:
        self._sock = sock
        self._addr = addr
        self._inbox = inbox
        self._seq_tx = 0
        self._seq_rx = 0

        if self._inbox is None:
            self._sock.settimeout(TIMEOUT)

    def enviar_mensaje(self, data: bytes) -> None:
        segmento = _build_segment(self._seq_tx, 0, data)
        reintentos = 0
        while True:
            self._sendto(segmento, self._addr)
            if self._esperar_ack(self._seq_tx):
                self._seq_tx = 1 - self._seq_tx
                return
            reintentos += 1
            if reintentos >= MAX_REINTENTOS:
                raise RuntimeError(
                    f"No se pudo entregar el mensaje tras {MAX_REINTENTOS} intentos."
                )

    def recibir_mensaje(self) -> bytes:
        intentos = 0
        while True:
            payload = self._esperar_segmento(self._seq_rx)
            if payload is not None:
                self._seq_rx = 1 - self._seq_rx
                return payload

            intentos += 1
            if intentos >= MAX_REINTENTOS:
                raise RuntimeError("No se pudo entregar el mensaje")

    def _sendto(self, data: bytes, addr: tuple) -> None:
        """Wrapper monkey-patcheable en tests."""
        self._sock.sendto(data, addr)

    def _recibir_raw(self) -> tuple[bytes, tuple]:
        if self._inbox is not None:
            try:
                return self._inbox.get(timeout=TIMEOUT)
            except queue.Empty as err:
                raise TimeoutError from err
        return self._sock.recvfrom(BUFFER_SIZE)

    def _esperar_ack(self, seq_esperado: int) -> bool:
        try:
            data, _ = self._recibir_raw()
        except (TimeoutError, socket.timeout, OSError):
            return False

        resultado = _parse_segment(data)
        if resultado is None:
            return False
        _, ack, _ = resultado
        return ack == seq_esperado

    def _esperar_segmento(self, seq_esperado: int) -> bytes | None:
        try:
            data, addr = self._recibir_raw()
        except (TimeoutError, socket.timeout):  # 👈 IMPORTANTE
            return None
        resultado = _parse_segment(data)
        if resultado is None:
            return None
        seq, _, payload = resultado
        if seq == seq_esperado:
            self._sock.sendto(_build_segment(0, seq_esperado, b""), addr)
            return payload
        self._sock.sendto(_build_segment(0, seq, b""), addr)
        return None
