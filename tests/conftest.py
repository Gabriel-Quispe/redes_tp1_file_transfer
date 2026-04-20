import os
import shutil
import socket
import threading
import time

import pytest

from server.dispatcher import ClientDispatcher
from server.listener import ServerListener
from server.socket import ServerSocket

# Valores alineados con los .feature files
STORAGE = "/tmp/storage"
DESTINO = "/tmp/destino"
HOST = "127.0.0.1"
PORT = 8000


@pytest.fixture(autouse=True)
def limpiar_carpetas():
    for path in [STORAGE, DESTINO]:
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path)
    yield
    for path in [STORAGE, DESTINO]:
        if os.path.exists(path):
            shutil.rmtree(path)


# Registro global para no levantar dos veces el mismo servidor en el mismo test
_servidores_activos: dict[tuple, dict] = {}
_servidores_lock = threading.Lock()


@pytest.fixture
def servidor_corriendo(request):
    """
    Levanta un servidor en HOST:PORT con STORAGE.
    Soporta que el step le pase host/port/storage distintos vía
    parametrize indirecto — pero en la práctica los features siempre
    usan 127.0.0.1:8000:/tmp/storage, que son las constantes de arriba.
    """
    host = HOST
    port = PORT
    storage = STORAGE

    server_socket = ServerSocket(host, port)
    dispatcher = ClientDispatcher(server_socket, storage)
    listener = ServerListener(server_socket, dispatcher)
    thread = threading.Thread(target=listener.start)
    thread.daemon = True
    thread.start()
    time.sleep(0.15)          # dar tiempo al thread para que el bind esté listo
    yield {"host": host, "port": port, "storage": storage}
    listener.stop()
    server_socket.close()
    time.sleep(0.05)          # pequeña pausa para que el SO libere el puerto


@pytest.fixture
def ctx():
    return {}


def crear_archivo_texto(path, contenido):
    if os.path.dirname(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(contenido)


def crear_archivo_binario(path, size_mb):
    data = os.urandom(size_mb * 1024 * 1024)
    with open(path, "wb") as f:
        f.write(data)
    return data


def poner_archivo_en_storage(nombre, contenido_bytes):
    path = os.path.join(STORAGE, nombre)
    with open(path, "wb") as f:
        f.write(contenido_bytes)
