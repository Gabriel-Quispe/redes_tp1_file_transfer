from abc import ABC, abstractmethod


class RDTProtocol(ABC):
    @abstractmethod
    def enviar_mensaje(self, data: bytes) -> None:
        """Envía bytes de forma confiable al otro extremo."""

    @abstractmethod
    def recibir_mensaje(self) -> bytes:
        """Bloquea hasta recibir el próximo mensaje y lo retorna como bytes."""
