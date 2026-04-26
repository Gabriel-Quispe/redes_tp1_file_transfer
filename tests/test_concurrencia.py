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

SRC          = sys.executable
UPLOAD_CMD   = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/upload"))
DOWNLOAD_CMD = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/download"))
FEATURE      = os.path.abspath(
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


@scenario(FEATURE, "Dos clientes usan protocolos distintos simultáneamente")
def test_dos_protocolos_distintos():
    pass


# ---------------------------------------------------------------------------
# Helpers de subprocess
# ---------------------------------------------------------------------------

def _run_upload(host, port, src, nombre, protocolo, results, key):
    result = subprocess.run(
        [SRC, UPLOAD_CMD, "-H", host, "-p", str(port), "-s", src,
         "-n", nombre, "-r", protocolo],
        capture_output=True,
        text=True,
    )
    results[key] = result


def _run_download(host, port, dst, nombre, protocolo, results, key):
    result = subprocess.run(
        [SRC, DOWNLOAD_CMD, "-H", host, "-p", str(port), "-d", dst,
         "-n", nombre, "-r", protocolo],
        capture_output=True,
        text=True,
    )
    results[key] = result


# ---------------------------------------------------------------------------
# Givens
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
        path   = f"/tmp/{nombre}"
        data   = crear_archivo_binario(path, size)
        ctx["archivos_paralelos"][nombre] = {"path": path, "data": data}


# ---------------------------------------------------------------------------
# Whens — escenarios originales
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
    ctx["results"]  = results
    ctx["nombre1"]  = nombre1
    ctx["nombre2"]  = nombre2


@when(
    parsers.parse(
        'el cliente 1 ejecuta upload de "{nombre_up}" y el cliente 2 ejecuta download de "{nombre_down}" en paralelo'
    )
)
def step_upload_y_download(ctx, nombre_up, nombre_down):
    results = {}
    t1 = threading.Thread(
        target=_run_upload,
        args=(HOST, PORT, f"/tmp/{nombre_up}", nombre_up, "stop_and_wait", results, "upload"),
    )
    t2 = threading.Thread(
        target=_run_download,
        args=(HOST, PORT, DESTINO, nombre_down, "stop_and_wait", results, "download"),
    )
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    ctx["results"]     = results
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

    from model.rdt.stop_and_wait.stop_and_wait import StopAndWait
    from model.app.messages.request_upload import RequestUploadMsg
    from model.codigos.cod_protocol import CodProtocol

    s = sock_module.socket(sock_module.AF_INET, sock_module.SOCK_DGRAM)
    s.bind(("0.0.0.0", 0))
    s.settimeout(2.0)
    rdt = StopAndWait(s, (HOST, PORT))
    try:
        msg = RequestUploadMsg(
            protocol=CodProtocol.STOP_AND_WAIT,
            filename="parcial.txt",
            filesize=100,
        ).to_bytes()
        rdt.enviar_mensaje(msg)
        rdt.recibir_mensaje()   # esperar OK del servidor (puede fallar)
    except Exception:
        pass
    finally:
        s.close()
    ctx["cliente_desconectado"] = True


# ---------------------------------------------------------------------------
# Whens — escenario 5 (protocolos distintos simultáneos)
# ---------------------------------------------------------------------------

@when(
    parsers.parse(
        'el cliente 1 ejecuta upload de "{nombre}" con protocolo "{protocolo}"'
    )
)
def step_cliente1_upload_async(ctx, nombre, protocolo):
    """Arranca el upload del cliente 1 en background; join se hace en el step And."""
    results = {}
    ctx["results_proto"]  = results
    ctx["nombres_proto"]  = [nombre]
    t = threading.Thread(
        target=_run_upload,
        args=(HOST, PORT, f"/tmp/{nombre}", nombre, protocolo, results, "c1"),
        daemon=True,
    )
    t.start()
    ctx["thread_c1"] = t


@when(
    parsers.parse(
        'el cliente 2 ejecuta upload de "{nombre}" con protocolo "{protocolo}" en paralelo'
    )
)
def step_cliente2_upload_sync(ctx, nombre, protocolo):
    """Arranca el upload del cliente 2 y espera a que ambos terminen."""
    results = ctx["results_proto"]
    ctx["nombres_proto"].append(nombre)
    t = threading.Thread(
        target=_run_upload,
        args=(HOST, PORT, f"/tmp/{nombre}", nombre, protocolo, results, "c2"),
        daemon=True,
    )
    t.start()
    ctx["thread_c1"].join()
    t.join()


# ---------------------------------------------------------------------------
# Thens — escenarios originales
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
        [SRC, UPLOAD_CMD, "-H", HOST, "-p", str(PORT),
         "-s", path, "-n", "check.txt", "-r", "stop_and_wait"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


# ---------------------------------------------------------------------------
# Thens — escenario 5 (protocolos distintos simultáneos)
# ---------------------------------------------------------------------------

@then("ambos archivos existen en el storage del servidor")
def step_ambos_existen(ctx):
    for nombre in ctx["nombres_proto"]:
        assert os.path.exists(os.path.join(STORAGE, nombre)), \
            f"Falta en storage: {nombre}"


@then("cada archivo es idéntico byte a byte al original")
def step_cada_identico_proto(ctx):
    for nombre in ctx["nombres_proto"]:
        expected = ctx.get("archivos", {}).get(nombre)
        if expected is None:
            continue   # no teníamos referencia local → sólo verificamos existencia
        with open(os.path.join(STORAGE, nombre), "rb") as f:
            assert f.read() == expected, f"Contenido de {nombre} no coincide"
