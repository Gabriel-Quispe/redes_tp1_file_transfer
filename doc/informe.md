# Introducción

......

# Hipótesis y suposiciones realizadas

......

# Implementación

El diseño del header se alinea en 4 palabras de 32 bits (Sumando un total de 16 Bytes), asegurando el uso del estándar Big-Endian
## Campos del Header:
1. __Opcode__ (1 Byte) que define el tipo de operación:
    * OP_START_UPLOAD   = 1 Inicio de la carga de archivos
    * OP_START_DOWNLOAD = 2 Inicio de la descarga de archivos
    * OP_DATA           = 3 
    * OP_ACK            = 4
    * OP_END            = 5 
    * OP_ERROR          = 6

2. __Padding__ (3 Bytes): Para alineación (sujeto a cambios y nuevas características).Este campo asegura que los campos definidos comiencen en direcciones de memoria alineadas, evitando overhead en el procesamiento de cada paquete
3. __Sequence Number__ (4 Bytes): Número de secuencia del paquete con soporte para 2³² segmentos
4. __Window Size__ (4 Bytes): para soportar el control de flujo en el servidor para múltiples clientes concurrentes
5. __Checksum__ (2 Bytes): Valor calculado sobre todo el paquete mediante CRC32 y truncado a 16 bits que soporta una verificación de integridad más robusta que la ofrecida por UDP.
6. __Payload Length__ (2 Bytes): 

```   0                               16                              32
      0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |    Opcode     |                    Padding                    |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |                        Sequence Number                        |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |                          Window Size                          |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
      |            Checksum           |         Payload Length        |
      +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```
......

# Pruebas

......

# Preguntas a responder

......

# Dificultades encontradas

......

# Conclusión

......
