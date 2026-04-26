import os
import shutil
import threading
import time

import pytest

from controller.server.dispatcher import ClientDispatcher
from controller.server.listener import ServerListener
from controller.server.socket import ServerSocket
from controller.server.registry import ClientRegistry


# Valores alineados con los .feature files
STORAGE = "/tmp/storage"
DESTINO = "/tmp/destino"
HOST    = "127.0.0.1"
PORT    = 8000


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


@pytest.fixture
def servidor_corriendo():
    """
    Levanta un servidor en HOST:PORT con STORAGE.
    Soporta que el step le pase host/port/storage distintos vía
    parametrize indirecto — pero en la práctica los features siempre
    usan 127.0.0.1:8000:/tmp/storage, que son las constantes de arriba.
    """
    server_socket = ServerSocket(HOST, PORT)
    registry      = ClientRegistry()
    dispatcher    = ClientDispatcher(server_socket, STORAGE, registry)
    listener      = ServerListener(server_socket, dispatcher)
    thread        = threading.Thread(target=listener.start)
    thread.daemon = True
    thread.start()
    time.sleep(0.15)   # dar tiempo al thread para que el bind esté listo
    yield {"host": HOST, "port": PORT, "storage": STORAGE}
    listener.stop()
    server_socket.close()
    time.sleep(0.05)   # pequeña pausa para que el SO libere el puerto


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
