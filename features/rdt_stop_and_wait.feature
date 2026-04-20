# language: es
Característica: Protocolo RDT Stop & Wait

  Escenario: Retransmisión ante timeout por pérdida de paquete de datos
    Dado que el cliente tiene un StopAndWait configurado con timeout de 0.5 segundos
    Y que el primer envío del segmento se pierde
    Cuando el cliente llama a enviar_mensaje con datos "hola"
    Entonces el cliente retransmite el segmento automáticamente
    Y el receptor recibe el mensaje "hola" correctamente

  Escenario: Retransmisión ante timeout por pérdida de ACK
    Dado que el cliente tiene un StopAndWait configurado con timeout de 0.5 segundos
    Y que el ACK del receptor se pierde
    Cuando el cliente llama a enviar_mensaje con datos "hola"
    Entonces el cliente retransmite el segmento
    Y el receptor descarta el duplicado silenciosamente
    Y el receptor reenvía el ACK
    Y el cliente recibe el ACK y avanza el número de secuencia

  Escenario: Descarte de segmento corrupto en el receptor
    Dado que el receptor tiene un StopAndWait esperando el segmento con seq 0
    Cuando llega un segmento con checksum inválido
    Entonces el receptor descarta el segmento silenciosamente
    Y no envía ningún ACK
    Y el emisor retransmite por timeout

  Escenario: Descarte de segmento duplicado en el receptor
    Dado que el receptor tiene un StopAndWait que ya recibió el segmento con seq 0
    Cuando llega nuevamente un segmento con seq 0
    Entonces el receptor reenvía el ACK 0
    Y no entrega el payload duplicado a la capa de aplicación

  Escenario: Falla definitiva tras MAX_REINTENTOS sin ACK
    Dado que el cliente tiene un StopAndWait configurado con timeout de 0.5 segundos
    Y que el receptor no responde en ningún intento
    Cuando el cliente llama a enviar_mensaje con datos "hola"
    Entonces el cliente lanza RuntimeError tras 10 intentos fallidos

  Escenario: Alternancia correcta del número de secuencia
    Dado que el cliente tiene un StopAndWait con seq_tx inicial 0
    Cuando el cliente envía el primer mensaje exitosamente
    Entonces seq_tx pasa a 1
    Cuando el cliente envía el segundo mensaje exitosamente
    Entonces seq_tx vuelve a 0

  Escenario: El servidor lee de la cola en vez del socket compartido
    Dado que el servidor tiene un StopAndWait en modo servidor con una Queue
    Cuando el dispatcher deposita un segmento en la Queue
    Entonces el StopAndWait del servidor lee de la Queue
    Y no interfiere con el ServerListener que lee del socket
