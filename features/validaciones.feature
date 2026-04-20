# language: es
Característica: Validaciones de parámetros

  Escenario: Host válido como IP
    Cuando valido el host "192.168.1.1"
    Entonces la validación pasa sin error

  Escenario: Host válido como hostname
    Cuando valido el host "localhost"
    Entonces la validación pasa sin error

  Escenario: Host inválido
    Cuando valido el host "host inv@lido!"
    Entonces la validación falla con el error "Invalid host"

  Escenario: Puerto válido en el límite inferior
    Cuando valido el puerto 1
    Entonces la validación pasa sin error

  Escenario: Puerto válido en el límite superior
    Cuando valido el puerto 65535
    Entonces la validación pasa sin error

  Escenario: Puerto fuera de rango inferior
    Cuando valido el puerto 0
    Entonces la validación falla con el error "Port must be between"

  Escenario: Puerto fuera de rango superior
    Cuando valido el puerto 99999
    Entonces la validación falla con el error "Port must be between"

  Escenario: Nombre de archivo válido
    Cuando valido el nombre "archivo.txt"
    Entonces la validación pasa sin error

  Escenario: Nombre de archivo vacío
    Cuando valido el nombre ""
    Entonces la validación falla con el error "Filename cannot be empty"

  Escenario: Nombre de archivo con caracteres inválidos
    Cuando valido el nombre "archi/vo.txt"
    Entonces la validación falla con el error "Invalid characters in filename"

  Escenario: Nombre de archivo con path traversal
    Cuando valido el nombre "../malicioso.txt"
    Entonces la validación falla con el error "Invalid characters in filename"

  Escenario: Protocolo válido stop_and_wait
    Cuando valido el protocolo "stop_and_wait"
    Entonces la validación pasa sin error

  Escenario: Protocolo válido selective_repeat
    Cuando valido el protocolo "selective_repeat"
    Entonces la validación pasa sin error

  Escenario: Protocolo inválido
    Cuando valido el protocolo "go_back_n"
    Entonces la validación falla con el error "Protocol must be one of"

  Escenario: Archivo de origen válido
    Dado que existe un archivo "/tmp/prueba.txt" con contenido "hola"
    Cuando valido el archivo "/tmp/prueba.txt"
    Entonces la validación pasa sin error

  Escenario: Archivo de origen inexistente
    Dado que no existe el archivo "/tmp/noexiste.txt"
    Cuando valido el archivo "/tmp/noexiste.txt"
    Entonces la validación falla con el error "File does not exist"

  Escenario: Carpeta de destino válida
    Dado que existe la carpeta "/tmp/destino"
    Cuando valido la carpeta "/tmp/destino"
    Entonces la validación pasa sin error

  Escenario: Carpeta de destino con padre inexistente
    Cuando valido la carpeta "/noexiste/destino"
    Entonces la validación falla con el error "Parent directory does not exist"
