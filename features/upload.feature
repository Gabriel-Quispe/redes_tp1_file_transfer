# language: es
Característica: Subida de archivos (Upload)

  Antecedentes:
    Dado que el servidor está corriendo en "127.0.0.1" puerto 8000 con storage "/tmp/storage"

  Escenario: Subida exitosa de un archivo de texto
    Dado que existe un archivo "/tmp/prueba.txt" con contenido "hola mundo"
    Cuando ejecuto upload con host "127.0.0.1" puerto 8000 src "/tmp/prueba.txt" nombre "prueba.txt" protocolo "stop_and_wait"
    Entonces el archivo "prueba.txt" existe en el storage del servidor
    Y el contenido del archivo en el servidor es "hola mundo"

  Escenario: Subida exitosa de un archivo binario
    Dado que existe un archivo binario "/tmp/imagen.png" de 1 MB
    Cuando ejecuto upload con host "127.0.0.1" puerto 8000 src "/tmp/imagen.png" nombre "imagen.png" protocolo "stop_and_wait"
    Entonces el archivo "imagen.png" existe en el storage del servidor
    Y el archivo en el servidor es idéntico byte a byte al original

  Escenario: Subida exitosa de un archivo de 5 MB en menos de 2 minutos
    Dado que existe un archivo binario "/tmp/grande.bin" de 5 MB
    Cuando ejecuto upload con host "127.0.0.1" puerto 8000 src "/tmp/grande.bin" nombre "grande.bin" protocolo "stop_and_wait"
    Entonces el upload finaliza en menos de 120 segundos
    Y el archivo "grande.bin" existe en el storage del servidor
    Y el archivo en el servidor es idéntico byte a byte al original

  Escenario: Error al subir un archivo que no existe en el cliente
    Dado que no existe el archivo "/tmp/inexistente.txt"
    Cuando ejecuto upload con host "127.0.0.1" puerto 8000 src "/tmp/inexistente.txt" nombre "inexistente.txt" protocolo "stop_and_wait"
    Entonces el comando falla con el error "File does not exist"

  Escenario: Error al subir con nombre de archivo inválido
    Dado que existe un archivo "/tmp/prueba.txt" con contenido "hola mundo"
    Cuando ejecuto upload con host "127.0.0.1" puerto 8000 src "/tmp/prueba.txt" nombre "../malicioso.txt" protocolo "stop_and_wait"
    Entonces el servidor responde con error "INVALID_FILENAME"
    Y no se guarda ningún archivo en el storage

  Escenario: Error al subir con puerto inválido
    Dado que existe un archivo "/tmp/prueba.txt" con contenido "hola mundo"
    Cuando ejecuto upload con host "127.0.0.1" puerto 99999 src "/tmp/prueba.txt" nombre "prueba.txt" protocolo "stop_and_wait"
    Entonces el comando falla con el error "Port must be between"

  Escenario: Error al subir con protocolo inválido
    Dado que existe un archivo "/tmp/prueba.txt" con contenido "hola mundo"
    Cuando ejecuto upload con host "127.0.0.1" puerto 8000 src "/tmp/prueba.txt" nombre "prueba.txt" protocolo "go_back_n"
    Entonces el comando falla con el error "invalid choice"

  Escenario: Subida con pérdida del 10% de paquetes
    Dado que existe un archivo "/tmp/prueba.txt" con contenido "hola mundo"
    Y la red tiene una pérdida de paquetes del 10%
    Cuando ejecuto upload con host "127.0.0.1" puerto 8000 src "/tmp/prueba.txt" nombre "prueba.txt" protocolo "stop_and_wait"
    Entonces el archivo "prueba.txt" existe en el storage del servidor
    Y el archivo en el servidor es idéntico byte a byte al original

  Escenario: Subida con paquetes corruptos
    Dado que existe un archivo "/tmp/prueba.txt" con contenido "hola mundo"
    Y la red corrompe el 5% de los paquetes
    Cuando ejecuto upload con host "127.0.0.1" puerto 8000 src "/tmp/prueba.txt" nombre "prueba.txt" protocolo "stop_and_wait"
    Entonces el archivo "prueba.txt" existe en el storage del servidor
    Y el archivo en el servidor es idéntico byte a byte al original

  Escenario: Error cuando el servidor no está disponible
    Dado que el servidor no está corriendo
    Y que existe un archivo "/tmp/prueba.txt" con contenido "hola mundo"
    Cuando ejecuto upload con host "127.0.0.1" puerto 8000 src "/tmp/prueba.txt" nombre "prueba.txt" protocolo "stop_and_wait"
    Entonces el comando falla con el error "No se pudo entregar el mensaje"
