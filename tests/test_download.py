import os
import subprocess
import sys
import time

from pytest_bdd import given, when, then, scenario, parsers

from conftest import STORAGE, poner_archivo_en_storage

SRC          = sys.executable
DOWNLOAD_CMD = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../src/download")
)
FEATURE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../features/download.feature")
)

SUBPROCESS_TIMEOUT = 35


@scenario(FEATURE, "Descarga exitosa de un archivo de texto")
def test_download_texto():
    pass


@scenario(FEATURE, "Descarga exitosa de un archivo binario")
def test_download_binario():
    pass


@scenario(FEATURE, "Descarga exitosa de un archivo de 5 MB en menos de 2 minutos")
def test_download_grande():
    pass


@scenario(FEATURE, "Error al descargar un archivo que no existe en el servidor")
def test_download_inexistente():
    pass


@scenario(FEATURE, "Error al descargar con carpeta destino sin permisos de escritura")
def test_download_sin_permisos():
    pass


@scenario(FEATURE, "Error al descargar con puerto inválido")
def test_download_puerto_invalido():
    pass


@scenario(FEATURE, "Error al descargar con protocolo inválido")
def test_download_protocolo_invalido():
    pass


@scenario(FEATURE, "Descarga con pérdida del 10% de paquetes")
def test_download_con_perdida():
    pass


@scenario(FEATURE, "Descarga con paquetes corruptos")
def test_download_con_corrupcion():
    pass


@scenario(FEATURE, "Error cuando el servidor no está disponible")
def test_download_sin_servidor():
    pass


# ---------------------------------------------------------------------------
# Givens
# ---------------------------------------------------------------------------

@given(
    parsers.parse(
        'que el servidor está corriendo en "{host}" puerto {port:d} con storage "{storage}"'
    )
)
def step_servidor_corriendo(servidor_corriendo):
    pass


@given(
    parsers.parse(
        'que el servidor tiene el archivo "{nombre}" con contenido "{contenido}"'
    )
)
def step_servidor_tiene_archivo(ctx, nombre, contenido):
    data = contenido.encode()
    poner_archivo_en_storage(nombre, data)
    ctx["nombre"]             = nombre
    ctx["contenido_original"] = data


@given(
    parsers.parse('que el servidor tiene el archivo binario "{nombre}" de {size:d} MB')
)
def step_servidor_tiene_binario(ctx, nombre, size):
    data = os.urandom(size * 1024 * 1024)
    poner_archivo_en_storage(nombre, data)
    ctx["nombre"]             = nombre
    ctx["contenido_original"] = data


@given(parsers.parse('que el servidor no tiene el archivo "{nombre}"'))
def step_servidor_no_tiene(ctx, nombre):
    path = os.path.join(STORAGE, nombre)
    if os.path.exists(path):
        os.remove(path)
    ctx["nombre"] = nombre


@given(parsers.parse('que existe la carpeta de destino "{path}"'))
def step_existe_carpeta(ctx, path):
    os.makedirs(path, exist_ok=True)
    ctx["dst"] = path


@given(
    parsers.parse('que la carpeta de destino "{path}" no tiene permisos de escritura')
)
def step_carpeta_sin_permisos(ctx, path):
    os.makedirs(path, exist_ok=True)
    os.chmod(path, 0o444)
    ctx["dst"] = path


@given("la red tiene una pérdida de paquetes del 10%")
def step_red_perdida(ctx):
    ctx["loss_rate"] = 0.10


@given("la red corrompe el 5% de los paquetes")
def step_red_corrupcion(ctx):
    ctx["corrupt_rate"] = 0.05


@given("que el servidor no está corriendo")
def step_sin_servidor(ctx):
    ctx["override_port"] = 19999


# ---------------------------------------------------------------------------
# Whens
# ---------------------------------------------------------------------------

@when(
    parsers.parse(
        'ejecuto download con host "{host}" puerto {port:d} dst "{dst}" '
        'nombre "{nombre}" protocolo "{protocolo}"'
    )
)
def step_ejecuto_download(ctx, host, port, dst, nombre, protocolo):
    port  = ctx.pop("override_port", port)
    dest  = ctx.get("dst", dst)
    start = time.time()
    try:
        result = subprocess.run(
            [SRC, DOWNLOAD_CMD,
             "-H", host,
             "-p", str(port),
             "-d", dest,
             "-n", nombre,
             "-r", protocolo],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
    except subprocess.TimeoutExpired as e:
        # Tratamos el timeout como fallo del comando (returncode != 0).
        result = subprocess.CompletedProcess(
            args=e.cmd,
            returncode=1,
            stdout="",
            stderr="[TIMEOUT] El comando no terminó en el tiempo esperado",
        )
    ctx["result"]  = result
    ctx["nombre"]  = ctx.get("nombre", nombre)
    ctx["dst"]     = dest
    ctx["elapsed"] = time.time() - start


# ---------------------------------------------------------------------------
# Thens
# ---------------------------------------------------------------------------

@then(parsers.parse('el archivo "{path}" existe'))
def step_archivo_existe(path):
    assert os.path.exists(path), f"No existe: {path}"


@then(parsers.parse('el contenido del archivo descargado es "{contenido}"'))
def step_contenido_descargado(ctx, contenido):
    path = os.path.join(ctx["dst"], ctx["nombre"])
    with open(path, "rb") as f:
        assert f.read() == contenido.encode()


@then("el archivo descargado es idéntico byte a byte al original en el servidor")
def step_identico_descargado(ctx):
    path = os.path.join(ctx["dst"], ctx["nombre"])
    with open(path, "rb") as f:
        assert f.read() == ctx["contenido_original"]


@then(parsers.parse("el download finaliza en menos de {segundos:d} segundos"))
def step_download_tiempo(ctx, segundos):
    assert ctx["elapsed"] < segundos, (
        f"Download tardó {ctx['elapsed']:.1f}s, límite {segundos}s"
    )


@then(parsers.parse('el comando falla con el error "{mensaje}"'))
def step_falla_con_error(ctx, mensaje):
    salida = ctx["result"].stdout + ctx["result"].stderr
    assert ctx["result"].returncode != 0 or mensaje in salida, (
        f"Se esperaba error '{mensaje}' pero la salida fue:\n{salida}"
    )


@then(parsers.parse('no se crea ningún archivo en "{path}"'))
def step_no_hay_archivo(path):
    if os.path.exists(path):
        archivos = [f for f in os.listdir(path) if not f.startswith(".")]
        assert len(archivos) == 0, f"Se encontraron archivos en {path}: {archivos}"
