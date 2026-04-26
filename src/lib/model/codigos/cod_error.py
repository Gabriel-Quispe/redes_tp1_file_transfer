from enum import IntEnum


class CodError(IntEnum):
    FILE_NOT_FOUND    = 0x01
    NO_SPACE          = 0x02
    INVALID_FILENAME  = 0x03
    USER_CANCELLED    = 0x04
    WRITE_ERROR       = 0x05
    FILESIZE_MISMATCH = 0x06
