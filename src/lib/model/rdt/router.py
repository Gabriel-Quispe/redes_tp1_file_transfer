import queue
import socket

from model.codigos.cod_protocol import CodProtocol
from model.rdt.rdt import RDTProtocol
from model.rdt.stop_and_wait.stop_and_wait import StopAndWait
from model.rdt.selective_repeat.selective_repeat import SelectiveRepeat


class RDTRouter(RDTProtocol):
    DEFAULT_PROTOCOL = CodProtocol.STOP_AND_WAIT

    def __init__(self, sock: socket.socket, addr: tuple, inbox: queue.Queue = None):
        self._sock             = sock
        self._addr             = addr
        self._inbox            = inbox
        self._current_protocol = self.DEFAULT_PROTOCOL
        self._rdt              = self._build(self.DEFAULT_PROTOCOL)

    def set_protocol(self, protocol: CodProtocol) -> None:
        if protocol == self._current_protocol:
            return

        seq_tx = self._get_seq_tx()
        seq_rx = self._get_seq_rx()

        new_rdt = self._build(protocol)
        self._set_seq_tx(new_rdt, seq_tx)
        self._set_seq_rx(new_rdt, seq_rx)

        self._rdt              = new_rdt
        self._current_protocol = protocol

    def enviar_mensaje(self, data: bytes) -> None:
        self._rdt.enviar_mensaje(data)

    def recibir_mensaje(self) -> bytes:
        return self._rdt.recibir_mensaje()

    # ------------------------------------------------------------------
    # Privados
    # ------------------------------------------------------------------

    def _build(self, protocol: CodProtocol) -> RDTProtocol:
        if protocol == CodProtocol.STOP_AND_WAIT:
            return StopAndWait(self._sock, self._addr, inbox=self._inbox)
        if protocol == CodProtocol.SELECTIVE_REPEAT:
            return SelectiveRepeat(self._sock, self._addr, inbox=self._inbox)
        raise ValueError(f"Protocolo desconocido: {protocol}")

    def _get_seq_tx(self) -> int:
        """Lee el próximo seq de envío del protocolo actual."""
        # StopAndWait usa _seq_tx; SelectiveRepeat usa _next_seq.
        if hasattr(self._rdt, '_seq_tx'):
            return self._rdt._seq_tx
        if hasattr(self._rdt, '_next_seq'):
            return self._rdt._next_seq
        return 0

    def _get_seq_rx(self) -> int:
        """Lee el próximo seq esperado de recepción del protocolo actual."""
        # StopAndWait usa _seq_rx; SelectiveRepeat usa _buffer.base.
        if hasattr(self._rdt, '_seq_rx'):
            return self._rdt._seq_rx
        if hasattr(self._rdt, '_buffer'):
            return self._rdt._buffer.base
        return 0

    @staticmethod
    def _set_seq_tx(rdt: RDTProtocol, value: int) -> None:
        if hasattr(rdt, '_seq_tx'):
            rdt._seq_tx = value
        elif hasattr(rdt, '_next_seq'):
            rdt._next_seq = value

    @staticmethod
    def _set_seq_rx(rdt: RDTProtocol, value: int) -> None:
        if hasattr(rdt, '_seq_rx'):
            rdt._seq_rx = value
        elif hasattr(rdt, '_buffer'):
            rdt._buffer._base = value
