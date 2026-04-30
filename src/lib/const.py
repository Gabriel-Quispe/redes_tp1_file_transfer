HEADER_FORMAT = "!B3xIIHH" #Tamaño del header
SV_MAX_WIN= 4000
SV_MAX_CLIENTS=10
SV_CLIENT_MIN_WIN=4

OP_START_UPLOAD   = 1
OP_START_DOWNLOAD = 2
OP_DATA           = 3
OP_ACK            = 4
OP_END            = 5  # Fin de transferencia
OP_ERROR          = 6

# Estos van en el primer paquete
PROTOCOL_SW = 1 #Stop n Wait 
PROTOCOL_SR  = 2 #Selective Repeat

# Para el sv 
MAX_PAYLOAD_SIZE = 1442
TIMEOUT          = 0.055
PORT=65535