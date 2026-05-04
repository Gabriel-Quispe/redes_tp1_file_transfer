# Introducción

......

# Hipótesis y suposiciones realizadas

......

# Implementación

El diseño del header se alinea en 4 palabras de 32 bits (Sumando un total de 16 Bytes), asegurando el uso del estándar Big-Endian
## Campos del Header:
1. __Opcode__ (1 Byte) que define el tipo de operación:
    * OP_START_UPLOAD   = 1: Inicio de la carga de archivos.
    * OP_START_DOWNLOAD = 2: Inicio de la descarga de archivos.
    * OP_DATA           = 3: Envio de datos Emisor->Receptor.
    * OP_ACK            = 4: Acknowledge Receptor->Emisor.
    * OP_END            = 5: Fin de transferencia.
    * OP_ERROR          = 6: Error.

2. __Padding__ (3 Bytes): Para alineación (sujeto a cambios y nuevas características). Este campo asegura que los campos definidos comiencen en direcciones de memoria alineadas, evitando overhead en el procesamiento de cada paquete.
3. __Sequence Number__ (4 Bytes): Número de secuencia del paquete con soporte para 2³² segmentos.
4. __Window Size__ (4 Bytes): para soportar el control de flujo en el servidor para múltiples clientes concurrentes.
5. __Checksum__ (2 Bytes): Valor calculado sobre todo el paquete mediante CRC32 y truncado a 16 bits que soporta una verificación de integridad más robusta que la ofrecida por UDP.
6. __Payload Length__ (2 Bytes):

## Formato de encabezado RFTP

```   0                               16                              31
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
Actualización dinámica del Retransmission Timeout por parte del lado emisor de datos. 

lbound = const.TIMEOUT
        ubound = 1.0    # 1s
        beta = 2
        rto = min(ubound, max(lbound, beta * rtt)) #Retransmission timeout
        # nuevo_timeout = (1-a) * old_timeout + a*rto
        self.timeout = 0.8 * self.timeout + 0.2*rto
¿Por qué el receptor no necesita un ajuste a su rto de forma dinámica? La función del receptor de datos es reaccionar a lo que llega. Si no llega nada, no tiene nada que retransmitir, por lo que no necesita una mejora de retransmisión. Usa un timeout genérico para no quedarse bloqueado eternamente

Es el emisor quien pone un paquete en la red y espera el ACK. El RTO dinámico (estimando el RTT con el algoritmo de Jacobson/Karn rfc 793) permite al emisor no esperar de más si la red está rápida, o no saturar la red si está lenta.

El tamaño de la ventana es fijo. Si bien el cliente siempre quiere poner la ventana máxima posible, cuando se acepta la conexión se establece la ventana minima priorizando al servidor. 
......

# Pruebas

......

# Preguntas a responder

......

# Dificultades encontradas

......

# Conclusión

......
