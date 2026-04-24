
#Implementar clase segmento, similar al TCP pero con menos parametros

class Segment:

	def __init__(self, src_port, dest_port):
		self.src_port = src_port
		self.dest_port = dest_port


import struct
import zlib

# En struct:        Bytes
# x= 1byte          1
# b= signed char    1
# B= unsigned char  1
# h= short          2
# H= unsigned short 2
# i/l= int/long     4
# I/L= unsigned int 4
# q= long long      8
# Q= unsigned long  8

# ! big-endian (byte order std de internet)

# OPCODE 1 Byte                 B (1 BYTE)
# Padding 3 bytes salteados     3x
# SEQ_NUMBER 4 Bytes -> 2³²     I (4 BYTES)
# WINDOW_SIZE                   I (4 BYTES)
# CHECKSUM                      H (2 BYTES)
# PAYLOAD_LEN                   H (2 BYTES)

#   0                               16                              32
#
#   0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2
#
#   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#
#   |    Opcode     |      Padding (para que lea en bloques)        |
#
#   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#
#   |                        Sequence Number                        |
#
#   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#
#   |                          Window Size                          |
#
#   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
#
#   |            Checksum           |         Payload Length        |
#
#   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
HEADER_FORMAT = "!B3xIIHH"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)  # 16 BYTES TOTALES


class Packet:
    def __init__(self, opcode, seq_num, wsize, payload):
        self.opcode = opcode
        self.seq_num = seq_num
        self.wsize = wsize
        self.payload = payload
        self.plen = len(payload)
        # self.chksum=0

    def pack(self):
        # header sin checksum
        header = struct.pack(HEADER_FORMAT, self.opcode, self.seq_num, self.wsize,0, self.plen)
        chksum = zlib.crc32(header + self.payload) & 0xFFFFFFFF & 0xFFFF #para evitar falsos negativos
        # header completo
        header =struct.pack(HEADER_FORMAT, self.opcode, self.seq_num, self.wsize, chksum, self.plen)
        return header + self.payload

    # Static para usarlo sin instanciar esta clase
    @staticmethod
    def unpack(data):
        """Fábrica que convierte los datos en un paquete"""
        if len(data) < HEADER_SIZE:
            raise ValueError("Paquete inválido: Demasiado pequeño")
        
        header = data[:HEADER_SIZE]
        payload = data[HEADER_SIZE:]
        opcode, seq_number, wsize, chksum, plen  = struct.unpack(HEADER_FORMAT, header)
        
        # CHECKSUM
        header_chk = struct.pack(HEADER_FORMAT, opcode, seq_number, wsize, 0, plen)
        chksum_received = zlib.crc32(header_chk + payload) & 0xFFFFFFFF
        
        if (chksum_received & 0xFFFF) != chksum:
            raise ValueError("Datos corruptos")

        payload = payload[:plen]
        return Packet(opcode, seq_number, wsize, payload)
