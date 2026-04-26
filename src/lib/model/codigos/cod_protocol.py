from enum import IntEnum


class CodProtocol(IntEnum):
    STOP_AND_WAIT = 0x01
    SELECTIVE_REPEAT = 0x02

    @classmethod
    def from_str(cls, name: str) -> "CodProtocol":
        mapping = {
            "stop_and_wait": cls.STOP_AND_WAIT,
            "selective_repeat": cls.SELECTIVE_REPEAT,
        }
        try:
            return mapping[name]
        except KeyError as err:
            raise ValueError(f"Protocolo desconocido: {name}") from err
