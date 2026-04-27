# language: es
Característica: Protocolo RDT Selective Repeat

  Escenario: Envío exitoso de un único mensaje con ventana
    Dado que el cliente tiene un SelectiveRepeat con ventana configurada
    Y que el receptor ACKea todos los segmentos
    Cuando el cliente llama a enviar_mensaje SR con datos "hola"
    Entonces el envío SR finaliza sin error
    Y el receptor SR recibe el mensaje "hola" correctamente

  Escenario: Retransmisión selectiva del segmento perdido
    Dado que el cliente tiene un SelectiveRepeat con ventana configurada
    Y que el segmento con seq 1 se pierde mientras 0 y 2 llegan bien
    Cuando el cliente llama a enviar_múltiples_mensajes SR con datos "A" "B" "C"
    Entonces solo el segmento con seq 1 es retransmitido
    Y los 3 mensajes son recibidos correctamente

  Escenario: Recepción fuera de orden con buffering
    Dado que el receptor tiene un SelectiveRepeat esperando el segmento con seq 0
    Cuando llegan los segmentos con seq 2 luego 0 luego 1
    Entonces el receptor entrega los mensajes en orden correcto

  Escenario: Descarte de segmento corrupto en el receptor SR
    Dado que el receptor tiene un SelectiveRepeat esperando el segmento con seq 0
    Cuando llega un segmento SR con checksum inválido
    Entonces el receptor SR descarta el segmento silenciosamente
    Y no envía ningún ACK SR
    Y el emisor SR retransmite por timeout

  Escenario: Segmento duplicado fuera de ventana es descartado
    Dado que el receptor tiene un SelectiveRepeat que ya entregó el segmento con seq 0
    Cuando llega nuevamente un segmento SR con seq 0
    Entonces el receptor SR descarta el duplicado silenciosamente
    Y no entrega el payload duplicado a la capa de aplicación

  Escenario: Falla definitiva tras MAX_REINTENTOS sin ACK
    Dado que el cliente tiene un SelectiveRepeat con ventana configurada
    Y que el receptor SR no responde en ningún intento
    Cuando el cliente llama a enviar_mensaje SR con datos "hola"
    Entonces el cliente SR lanza RuntimeError tras agotar los reintentos

  Escenario: La ventana avanza al recibir ACKs en orden
    Dado que el cliente tiene un SelectiveRepeat con ventana configurada
    Y que el receptor ACKea todos los segmentos
    Cuando el cliente envía 4 mensajes SR exitosamente
    Entonces la base de la ventana avanza al valor 4

  Escenario: ACK fuera de ventana es ignorado
    Dado que el receptor tiene un SelectiveRepeat esperando el segmento con seq 0
    Cuando llega un ACK SR con número de seq 99
    Entonces el receptor SR ignora el ACK fuera de ventana sin error

  Escenario: El servidor SR lee de la cola en vez del socket compartido
    Dado que el servidor tiene un SelectiveRepeat en modo servidor con una Queue
    Cuando el dispatcher deposita un segmento SR en la Queue
    Entonces el SelectiveRepeat del servidor lee de la Queue
    Y no interfiere con el ServerListener que lee del socket
