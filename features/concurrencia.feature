# language: es
Característica: Concurrencia del servidor

  Antecedentes:
    Dado que el servidor está corriendo en "127.0.0.1" puerto 8000 con storage "/tmp/storage"

  Escenario: Dos clientes suben archivos distintos simultáneamente
    Dado que existe un archivo "/tmp/archivo1.txt" con contenido "cliente uno"
    Y que existe un archivo "/tmp/archivo2.txt" con contenido "cliente dos"
    Cuando el cliente 1 ejecuta upload de "archivo1.txt" y el cliente 2 ejecuta upload de "archivo2.txt" en paralelo
    Entonces el archivo "archivo1.txt" existe en el storage del servidor con contenido "cliente uno"
    Y el archivo "archivo2.txt" existe en el storage del servidor con contenido "cliente dos"

  Escenario: Un cliente sube y otro descarga simultáneamente
    Dado que el servidor tiene el archivo "existente.txt" con contenido "ya estaba"
    Y que existe un archivo "/tmp/nuevo.txt" con contenido "recién subido"
    Cuando el cliente 1 ejecuta upload de "nuevo.txt" y el cliente 2 ejecuta download de "existente.txt" en paralelo
    Entonces el archivo "nuevo.txt" existe en el storage del servidor
    Y el cliente 2 recibe el archivo "existente.txt" con contenido "ya estaba"

  Escenario: Cinco clientes suben archivos simultáneamente
    Dado que existen 5 archivos de prueba de 1 MB cada uno
    Cuando los 5 clientes ejecutan upload en paralelo con protocolo "stop_and_wait"
    Entonces los 5 archivos existen en el storage del servidor
    Y cada archivo en el servidor es idéntico byte a byte al original

  Escenario: Cliente que se desconecta a mitad de un upload
    Dado que existe un archivo "/tmp/prueba.txt" con contenido "hola mundo"
    Cuando el cliente inicia un upload y se desconecta antes de enviar los datos
    Entonces el servidor no guarda ningún archivo parcial
    Y el servidor sigue disponible para nuevos clientes

  Escenario: Dos clientes usan protocolos distintos simultáneamente
    Dado que existe un archivo "/tmp/saw.txt" con contenido "stop and wait"
    Y que existe un archivo "/tmp/sr.txt" con contenido "selective repeat"
    Cuando el cliente 1 ejecuta upload de "saw.txt" con protocolo "stop_and_wait"
    Y el cliente 2 ejecuta upload de "sr.txt" con protocolo "selective_repeat" en paralelo
    Entonces ambos archivos existen en el storage del servidor
    Y cada archivo es idéntico byte a byte al original
