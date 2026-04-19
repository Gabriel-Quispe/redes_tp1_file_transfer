import socket
import struct

from app.rdt.rdt import RDTProtocol

# ---------------------------------------------------------------------------
# Constantes internas de S&W
# ---------------------------------------------------------------------------

TIMEOUT = 0.5  # segundos antes de retransmitir
MAX_REINTENTOS = 10  # intentos máximos antes de declarar falla
BUFFER_SIZE = 65535  # tamaño máximo de lectura UDP
HEADER_SIZE = 4  # SEQ(1) + ACK(1) + CKSUM(2)

SEQ_DATA = 0xFF  # segmento que transporta datos
SEQ_ACK = 0x00  # segmento que solo transporta confirmación


# ---------------------------------------------------------------------------
# Helpers de checksum
# ---------------------------------------------------------------------------


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
    """Construye un segmento RDT con checksum calculado."""
    header_sin_cksum = bytes([seq, ack]) + b"\x00\x00"
    cksum = _crc16(header_sin_cksum + payload)
    header = bytes([seq, ack]) + struct.pack("!H", cksum)
    return header + payload


def _parse_segment(data: bytes) -> tuple[int, int, bytes] | None:
    """
    Parsea un segmento RDT.
    Retorna (seq, ack, payload) si el checksum es válido.
    Retorna None si el segmento está corrupto.
    """
    if len(data) < HEADER_SIZE:
        return None

    seq, ack = data[0], data[1]
    cksum_recibido = struct.unpack("!H", data[2:4])[0]
    payload = data[HEADER_SIZE:]

    # Recalcular checksum con los mismos bytes
    header_sin_cksum = bytes([seq, ack]) + b"\x00\x00"
    cksum_esperado = _crc16(header_sin_cksum + payload)

    if cksum_recibido != cksum_esperado:
        return None  # segmento corrupto, descartar

    return seq, ack, payload


# ---------------------------------------------------------------------------
# Stop & Wait
# ---------------------------------------------------------------------------


class StopAndWait(RDTProtocol):
    """
    Implementación de Stop & Wait sobre UDP.

    Garantiza a la capa de aplicación:
      - Entrega confiable (retransmisión por timeout)
      - Sin duplicados (número de secuencia alternante)
      - Orden (S&W es inherentemente ordenado)
      - Detección de corrupción (CRC-16)

    La capa de aplicación solo llama a enviar_mensaje() y recibir_mensaje().
    No sabe nada de SEQ, ACK, timeouts ni retransmisiones.
    """

    def __init__(self, sock: socket.socket, addr: tuple[str, int]) -> None:
        self._sock = sock
        self._addr = addr
        self._seq_tx = 0  # número de secuencia del próximo envío
        self._seq_rx = 0  # número de secuencia que espero recibir

        self._sock.settimeout(TIMEOUT)

    # ------------------------------------------------------------------
    # Interfaz pública (lo único que ve la capa de aplicación)
    # ------------------------------------------------------------------

    def enviar_mensaje(self, data: bytes) -> None:
        """
        Envía data de forma confiable.
        Retransmite hasta MAX_REINTENTOS veces ante timeout o corrupción.
        Lanza RuntimeError si no se puede entregar el mensaje.
        """
        segmento = _build_segment(self._seq_tx, 0, data)
        reintentos = 0

        while True:
            self._sock.sendto(segmento, self._addr)

            ack_recibido = self._esperar_ack(self._seq_tx)
            if ack_recibido:
                # ACK correcto: avanzar número de secuencia
                self._seq_tx = 1 - self._seq_tx
                return

            reintentos += 1
            if reintentos >= MAX_REINTENTOS:
                raise RuntimeError(
                    f"No se pudo entregar el mensaje tras {MAX_REINTENTOS} intentos."
                )

    def recibir_mensaje(self) -> bytes:
        """
        Bloquea hasta recibir el próximo mensaje en orden.
        Descarta duplicados y segmentos corruptos silenciosamente.
        Retorna el payload limpio a la capa de aplicación.
        """
        while True:
            payload = self._esperar_segmento(self._seq_rx)
            if payload is None:
                continue

            # Segmento válido y en orden: avanzar y retornar a la app
            self._seq_rx = 1 - self._seq_rx
            return payload

    # ------------------------------------------------------------------
    # Lógica interna
    # ------------------------------------------------------------------

    def _esperar_ack(self, seq_esperado: int) -> bool:
        """
        Espera un ACK para el seq dado.
        Retorna True si llega el ACK correcto.
        Retorna False si hay timeout.
        """
        try:
            data, _ = self._sock.recvfrom(BUFFER_SIZE)
        except TimeoutError:
            return False

        resultado = _parse_segment(data)
        if resultado is None:
            return False  # corrupto, ignorar

        _, ack, _ = resultado
        return ack == seq_esperado

    def _esperar_segmento(self, seq_esperado: int) -> bytes | None:
        """
        Espera un segmento de datos con el seq esperado.
        - Si llega el segmento correcto: envía ACK y retorna payload.
        - Si llega un duplicado (seq anterior): reenvía ACK pero retorna None.
        - Si llega corrupto: descarta silenciosamente, retorna None.
        """
        try:
            data, addr = self._sock.recvfrom(BUFFER_SIZE)
        except TimeoutError:
            return None

        resultado = _parse_segment(data)
        if resultado is None:
            return None  # corrupto, descartar

        seq, _, payload = resultado

        if seq == seq_esperado:
            # Segmento nuevo y en orden: confirmar y entregar
            ack = _build_segment(0, seq_esperado, b"")
            self._sock.sendto(ack, addr)
            return payload

        # Duplicado: el ACK anterior se perdió, reenviar
        ack = _build_segment(0, seq, b"")
        self._sock.sendto(ack, addr)
        return None
