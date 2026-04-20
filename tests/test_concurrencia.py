import os
import subprocess
import sys
import threading

from pytest_bdd import given, when, then, scenario, parsers

from conftest import (
    STORAGE,
    DESTINO,
    HOST,
    PORT,
    crear_archivo_texto,
    crear_archivo_binario,
    poner_archivo_en_storage,
)

SRC = sys.executable
UPLOAD_CMD = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/upload"))
DOWNLOAD_CMD = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../src/download")
)
FEATURE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../features/concurrencia.feature")
)


@scenario(FEATURE, "Dos clientes suben archivos distintos simultáneamente")
def test_dos_uploads_paralelos():
    pass


@scenario(FEATURE, "Un cliente sube y otro descarga simultáneamente")
def test_upload_y_download_paralelos():
    pass


@scenario(FEATURE, "Cinco clientes suben archivos simultáneamente")
def test_cinco_uploads_paralelos():
    pass


@scenario(FEATURE, "Cliente que se desconecta a mitad de un upload")
def test_cliente_desconectado():
    pass


def _run_upload(host, port, src, nombre, protocolo, results, key):
    result = subprocess.run(
        [
            SRC,
            UPLOAD_CMD,
            "-H",
            host,
            "-p",
            str(port),
            "-s",
            src,
            "-n",
            nombre,
            "-r",
            protocolo,
        ],
        capture_output=True,
        text=True,
    )
    results[key] = result


def _run_download(host, port, dst, nombre, protocolo, results, key):
    result = subprocess.run(
        [
            SRC,
            DOWNLOAD_CMD,
            "-H",
            host,
            "-p",
            str(port),
            "-d",
            dst,
            "-n",
            nombre,
            "-r",
            protocolo,
        ],
        capture_output=True,
        text=True,
    )
    results[key] = result


# ---------------------------------------------------------------------------
# Givens
# FIX: "Dado que X" in Antecedentes/scenarios → step text "que X".
# ---------------------------------------------------------------------------


@given(
    parsers.parse(
        'que el servidor está corriendo en "{host}" puerto {port:d} con storage "{storage}"'
    )
)
def step_servidor(servidor_corriendo):
    pass


@given(parsers.parse('que existe un archivo "{path}" con contenido "{contenido}"'))
def step_existe_archivo(ctx, path, contenido):
    crear_archivo_texto(path, contenido)
    ctx.setdefault("archivos", {})[os.path.basename(path)] = contenido.encode()


@given(
    parsers.parse(
        'que el servidor tiene el archivo "{nombre}" con contenido "{contenido}"'
    )
)
def step_servidor_tiene(ctx, nombre, contenido):
    poner_archivo_en_storage(nombre, contenido.encode())
    ctx.setdefault("archivos_servidor", {})[nombre] = contenido.encode()


@given(parsers.parse("que existen {n:d} archivos de prueba de {size:d} MB cada uno"))
def step_n_archivos(ctx, n, size):
    ctx["archivos_paralelos"] = {}
    for i in range(n):
        nombre = f"paralelo_{i}.bin"
        path = f"/tmp/{nombre}"
        data = crear_archivo_binario(path, size)
        ctx["archivos_paralelos"][nombre] = {"path": path, "data": data}


# ---------------------------------------------------------------------------
# Whens
# ---------------------------------------------------------------------------


@when(
    parsers.parse(
        'el cliente 1 ejecuta upload de "{nombre1}" y el cliente 2 ejecuta upload de "{nombre2}" en paralelo'
    )
)
def step_dos_uploads(ctx, nombre1, nombre2):
    results = {}
    t1 = threading.Thread(
        target=_run_upload,
        args=(HOST, PORT, f"/tmp/{nombre1}", nombre1, "stop_and_wait", results, "c1"),
    )
    t2 = threading.Thread(
        target=_run_upload,
        args=(HOST, PORT, f"/tmp/{nombre2}", nombre2, "stop_and_wait", results, "c2"),
    )
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    ctx["results"] = results
    ctx["nombre1"] = nombre1
    ctx["nombre2"] = nombre2


@when(
    parsers.parse(
        'el cliente 1 ejecuta upload de "{nombre_up}" y el cliente 2 ejecuta download de "{nombre_down}" en paralelo'
    )
)
def step_upload_y_download(ctx, nombre_up, nombre_down):
    results = {}
    t1 = threading.Thread(
        target=_run_upload,
        args=(
            HOST,
            PORT,
            f"/tmp/{nombre_up}",
            nombre_up,
            "stop_and_wait",
            results,
            "upload",
        ),
    )
    t2 = threading.Thread(
        target=_run_download,
        args=(HOST, PORT, DESTINO, nombre_down, "stop_and_wait", results, "download"),
    )
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    ctx["results"] = results
    ctx["nombre_down"] = nombre_down


@when(
    parsers.parse(
        'los {n:d} clientes ejecutan upload en paralelo con protocolo "{protocolo}"'
    )
)
def step_n_uploads(ctx, n, protocolo):
    results = {}
    threads = [
        threading.Thread(
            target=_run_upload,
            args=(HOST, PORT, info["path"], nombre, protocolo, results, nombre),
        )
        for nombre, info in ctx["archivos_paralelos"].items()
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    ctx["results"] = results


@when("el cliente inicia un upload y se desconecta antes de enviar los datos")
def step_cliente_desconectado(ctx):
    import socket as sock_module
    from app.rdt.stop_and_wait import StopAndWait
    from app.msj_serializer import MessageSerializer

    s = sock_module.socket(sock_module.AF_INET, sock_module.SOCK_DGRAM)
    s.bind(("0.0.0.0", 0))
    serializer = MessageSerializer()
    rdt = StopAndWait(s, (HOST, PORT))
    try:
        rdt.enviar_mensaje(serializer.build_request_upload("parcial.txt", 100))
        rdt.recibir_mensaje()
    except Exception:
        pass
    finally:
        s.close()
    ctx["cliente_desconectado"] = True


# ---------------------------------------------------------------------------
# Thens
# ---------------------------------------------------------------------------


@then(
    parsers.parse(
        'el archivo "{nombre}" existe en el storage del servidor con contenido "{contenido}"'
    )
)
def step_archivo_storage_contenido(nombre, contenido):
    path = os.path.join(STORAGE, nombre)
    assert os.path.exists(path)
    with open(path, "rb") as f:
        assert f.read() == contenido.encode()


@then(parsers.parse('el archivo "{nombre}" existe en el storage del servidor'))
def step_archivo_en_storage(nombre):
    assert os.path.exists(os.path.join(STORAGE, nombre))


@then(
    parsers.parse(
        'el cliente 2 recibe el archivo "{nombre}" con contenido "{contenido}"'
    )
)
def step_cliente2_recibe(ctx, nombre, contenido):
    path = os.path.join(DESTINO, nombre)
    assert os.path.exists(path)
    with open(path, "rb") as f:
        assert f.read() == contenido.encode()


@then("los 5 archivos existen en el storage del servidor")
def step_5_archivos(ctx):
    for nombre in ctx["archivos_paralelos"]:
        assert os.path.exists(os.path.join(STORAGE, nombre))


@then("cada archivo en el servidor es idéntico byte a byte al original")
def step_cada_identico(ctx):
    for nombre, info in ctx["archivos_paralelos"].items():
        with open(os.path.join(STORAGE, nombre), "rb") as f:
            assert f.read() == info["data"]


@then("el servidor no guarda ningún archivo parcial")
def step_sin_parcial():
    assert "parcial.txt" not in os.listdir(STORAGE)


@then("el servidor sigue disponible para nuevos clientes")
def step_servidor_disponible(servidor_corriendo):
    path = "/tmp/check.txt"
    crear_archivo_texto(path, "check")
    result = subprocess.run(
        [
            SRC,
            UPLOAD_CMD,
            "-H",
            HOST,
            "-p",
            str(PORT),
            "-s",
            path,
            "-n",
            "check.txt",
            "-r",
            "stop_and_wait",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
