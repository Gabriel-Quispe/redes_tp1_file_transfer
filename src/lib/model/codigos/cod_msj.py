from enum import IntEnum


class CodMsj(IntEnum):
    REQUEST = 0x01
    RESPONSE = 0x02
    DATA = 0x03
    ERR = 0x04
