import os
import subprocess
import sys
import time

import pytest
from pytest_bdd import given, when, then, scenario, parsers

from conftest import STORAGE, DESTINO, HOST, PORT, crear_archivo_texto, crear_archivo_binario

SRC = sys.executable
UPLOAD_CMD = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/upload"))
FEATURE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../features/upload.feature"))


@scenario(FEATURE, "Subida exitosa de un archivo de texto")
def test_upload_texto(): pass

@scenario(FEATURE, "Subida exitosa de un archivo binario")
def test_upload_binario(): pass

@scenario(FEATURE, "Subida exitosa de un archivo de 5 MB en menos de 2 minutos")
def test_upload_grande(): pass

@scenario(FEATURE, "Error al subir un archivo que no existe en el cliente")
def test_upload_archivo_inexistente(): pass

@scenario(FEATURE, "Error al subir con nombre de archivo inválido")
def test_upload_nombre_invalido(): pass

@scenario(FEATURE, "Error al subir con puerto inválido")
def test_upload_puerto_invalido(): pass

@scenario(FEATURE, "Error al subir con protocolo inválido")
def test_upload_protocolo_invalido(): pass

@scenario(FEATURE, "Subida con pérdida del 10% de paquetes")
def test_upload_con_perdida(): pass

@scenario(FEATURE, "Subida con paquetes corruptos")
def test_upload_con_corrupcion(): pass

@scenario(FEATURE, "Error cuando el servidor no está disponible")
def test_upload_sin_servidor(): pass


# ---------------------------------------------------------------------------
# Givens
# FIX: "Dado que X" in Antecedentes → step text "que X". Add "que " prefix.
# ---------------------------------------------------------------------------

@given(parsers.parse('que el servidor está corriendo en "{host}" puerto {port:d} con storage "{storage}"'))
def step_servidor_corriendo(servidor_corriendo):
    pass


@given(parsers.parse('que existe un archivo "{path}" con contenido "{contenido}"'))
def step_existe_archivo_texto(ctx, path, contenido):
    crear_archivo_texto(path, contenido)
    ctx["src"] = path
    ctx["contenido"] = contenido.encode()


@given(parsers.parse('que existe un archivo binario "{path}" de {size:d} MB'))
def step_existe_archivo_binario(ctx, path, size):
    data = crear_archivo_binario(path, size)
    ctx["src"] = path
    ctx["contenido"] = data


@given(parsers.parse('que no existe el archivo "{path}"'))
def step_no_existe_archivo(ctx, path):
    if os.path.exists(path):
        os.remove(path)
    ctx["src"] = path


@given("la red tiene una pérdida de paquetes del 10%")
def step_red_con_perdida(ctx):
    ctx["loss_rate"] = 0.10


@given("la red corrompe el 5% de los paquetes")
def step_red_con_corrupcion(ctx):
    ctx["corrupt_rate"] = 0.05


@given("que el servidor no está corriendo")
def step_servidor_no_corriendo(ctx):
    # Usamos un puerto donde seguro no hay servidor
    ctx["override_port"] = 19999

# ---------------------------------------------------------------------------
# Whens
# ---------------------------------------------------------------------------

@when(parsers.parse(
    'ejecuto upload con host "{host}" puerto {port:d} src "{src}" nombre "{nombre}" protocolo "{protocolo}"'
))
def step_ejecuto_upload(ctx, host, port, src, nombre, protocolo):
    port = ctx.pop("override_port", port)   # <-- usa el puerto override si existe
    start = time.time()
    result = subprocess.run(
        [SRC, UPLOAD_CMD, "-H", host, "-p", str(port), "-s", src, "-n", nombre, "-r", protocolo],
        capture_output=True, text=True
    )
    ctx["result"] = result
    ctx["nombre"] = nombre
    ctx["elapsed"] = time.time() - start


# ---------------------------------------------------------------------------
# Thens
# ---------------------------------------------------------------------------

@then(parsers.parse('el archivo "{nombre}" existe en el storage del servidor'))
def step_archivo_en_storage(nombre):
    path = os.path.join(STORAGE, nombre)
    assert os.path.exists(path), f"El archivo {nombre} no existe en el storage"


@then(parsers.parse('el contenido del archivo en el servidor es "{contenido}"'))
def step_contenido_en_servidor(ctx, contenido):
    path = os.path.join(STORAGE, ctx["nombre"])
    with open(path, "rb") as f:
        assert f.read() == contenido.encode()


@then("el archivo en el servidor es idéntico byte a byte al original")
def step_identico_en_servidor(ctx):
    path = os.path.join(STORAGE, ctx["nombre"])
    with open(path, "rb") as f:
        assert f.read() == ctx["contenido"]


@then(parsers.parse("el upload finaliza en menos de {segundos:d} segundos"))
def step_upload_tiempo(ctx, segundos):
    assert ctx["elapsed"] < segundos


@then(parsers.parse('el comando falla con el error "{mensaje}"'))
def step_comando_falla(ctx, mensaje):
    result = ctx["result"]
    salida = result.stdout + result.stderr
    assert result.returncode != 0 or mensaje in salida, \
        f"Se esperaba error '{mensaje}' pero la salida fue: {salida}"


@then(parsers.parse('el servidor responde con error "{codigo}"'))
def step_servidor_error(ctx, codigo):
    salida = ctx["result"].stdout + ctx["result"].stderr
    assert codigo in salida


@then("no se guarda ningún archivo en el storage")
def step_storage_vacio():
    assert len(os.listdir(STORAGE)) == 0
