# language: es
Característica: Descarga de archivos (Download)

  Antecedentes:
    Dado que el servidor está corriendo en "127.0.0.1" puerto 8000 con storage "/tmp/storage"

  Escenario: Descarga exitosa de un archivo de texto
    Dado que el servidor tiene el archivo "prueba.txt" con contenido "hola mundo"
    Y que existe la carpeta de destino "/tmp/destino"
    Cuando ejecuto download con host "127.0.0.1" puerto 8000 dst "/tmp/destino" nombre "prueba.txt" protocolo "stop_and_wait"
    Entonces el archivo "/tmp/destino/prueba.txt" existe
    Y el contenido del archivo descargado es "hola mundo"

  Escenario: Descarga exitosa de un archivo binario
    Dado que el servidor tiene el archivo binario "imagen.png" de 1 MB
    Y que existe la carpeta de destino "/tmp/destino"
    Cuando ejecuto download con host "127.0.0.1" puerto 8000 dst "/tmp/destino" nombre "imagen.png" protocolo "stop_and_wait"
    Entonces el archivo "/tmp/destino/imagen.png" existe
    Y el archivo descargado es idéntico byte a byte al original en el servidor

  Escenario: Descarga exitosa de un archivo de 5 MB en menos de 2 minutos
    Dado que el servidor tiene el archivo binario "grande.bin" de 5 MB
    Y que existe la carpeta de destino "/tmp/destino"
    Cuando ejecuto download con host "127.0.0.1" puerto 8000 dst "/tmp/destino" nombre "grande.bin" protocolo "stop_and_wait"
    Entonces el download finaliza en menos de 120 segundos
    Y el archivo descargado es idéntico byte a byte al original en el servidor

  Escenario: Error al descargar un archivo que no existe en el servidor
    Dado que el servidor no tiene el archivo "noexiste.txt"
    Y que existe la carpeta de destino "/tmp/destino"
    Cuando ejecuto download con host "127.0.0.1" puerto 8000 dst "/tmp/destino" nombre "noexiste.txt" protocolo "stop_and_wait"
    Entonces el comando falla con el error "FILE_NOT_FOUND"
    Y no se crea ningún archivo en "/tmp/destino"

  Escenario: Error al descargar con carpeta destino sin permisos de escritura
    Dado que el servidor tiene el archivo "prueba.txt" con contenido "hola mundo"
    Y que la carpeta de destino "/tmp/sinpermisos" no tiene permisos de escritura
    Cuando ejecuto download con host "127.0.0.1" puerto 8000 dst "/tmp/sinpermisos" nombre "prueba.txt" protocolo "stop_and_wait"
    Entonces el comando falla con el error "No write permission"

  Escenario: Error al descargar con puerto inválido
    Dado que el servidor tiene el archivo "prueba.txt" con contenido "hola mundo"
    Cuando ejecuto download con host "127.0.0.1" puerto 99999 dst "/tmp/destino" nombre "prueba.txt" protocolo "stop_and_wait"
    Entonces el comando falla con el error "Port must be between"

  Escenario: Error al descargar con protocolo inválido
    Dado que el servidor tiene el archivo "prueba.txt" con contenido "hola mundo"
    Cuando ejecuto download con host "127.0.0.1" puerto 8000 dst "/tmp/destino" nombre "prueba.txt" protocolo "go_back_n"
    Entonces el comando falla con el error "invalid choice"

  Escenario: Descarga con pérdida del 10% de paquetes
    Dado que el servidor tiene el archivo "prueba.txt" con contenido "hola mundo"
    Y que existe la carpeta de destino "/tmp/destino"
    Y la red tiene una pérdida de paquetes del 10%
    Cuando ejecuto download con host "127.0.0.1" puerto 8000 dst "/tmp/destino" nombre "prueba.txt" protocolo "stop_and_wait"
    Entonces el archivo "/tmp/destino/prueba.txt" existe
    Y el archivo descargado es idéntico byte a byte al original en el servidor

  Escenario: Descarga con paquetes corruptos
    Dado que el servidor tiene el archivo "prueba.txt" con contenido "hola mundo"
    Y que existe la carpeta de destino "/tmp/destino"
    Y la red corrompe el 5% de los paquetes
    Cuando ejecuto download con host "127.0.0.1" puerto 8000 dst "/tmp/destino" nombre "prueba.txt" protocolo "stop_and_wait"
    Entonces el archivo "/tmp/destino/prueba.txt" existe
    Y el archivo descargado es idéntico byte a byte al original en el servidor

  Escenario: Error cuando el servidor no está disponible
    Dado que el servidor no está corriendo
    Y que existe la carpeta de destino "/tmp/destino"
    Cuando ejecuto download con host "127.0.0.1" puerto 8000 dst "/tmp/destino" nombre "prueba.txt" protocolo "stop_and_wait"
    Entonces el comando falla con el error "No se pudo entregar el mensaje"
