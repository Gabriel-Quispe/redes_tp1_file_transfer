import os

from pytest_bdd import given, when, then, scenario, parsers

from view.validations.host import HostValidation
from view.validations.port import PortValidation
from view.validations.name import NameValidation
from view.validations.protocol import ProtocolValidation
from view.validations.file import FileValidation
from view.validations.folder import FolderValidation

FEATURE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../features/validaciones.feature")
)


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

@scenario(FEATURE, "Host válido como IP")
def test_host_ip():
    pass


@scenario(FEATURE, "Host válido como hostname")
def test_host_hostname():
    pass


@scenario(FEATURE, "Host inválido")
def test_host_invalido():
    pass


@scenario(FEATURE, "Puerto válido en el límite inferior")
def test_puerto_min():
    pass


@scenario(FEATURE, "Puerto válido en el límite superior")
def test_puerto_max():
    pass


@scenario(FEATURE, "Puerto fuera de rango inferior")
def test_puerto_bajo():
    pass


@scenario(FEATURE, "Puerto fuera de rango superior")
def test_puerto_alto():
    pass


@scenario(FEATURE, "Nombre de archivo válido")
def test_nombre_valido():
    pass


@scenario(FEATURE, "Nombre de archivo vacío")
def test_nombre_vacio():
    pass


@scenario(FEATURE, "Nombre de archivo con caracteres inválidos")
def test_nombre_invalido():
    pass


@scenario(FEATURE, "Nombre de archivo con path traversal")
def test_nombre_traversal():
    pass


@scenario(FEATURE, "Protocolo válido stop_and_wait")
def test_protocolo_saw():
    pass


@scenario(FEATURE, "Protocolo válido selective_repeat")
def test_protocolo_sr():
    pass


@scenario(FEATURE, "Protocolo inválido")
def test_protocolo_invalido():
    pass


@scenario(FEATURE, "Archivo de origen válido")
def test_archivo_valido():
    pass


@scenario(FEATURE, "Archivo de origen inexistente")
def test_archivo_inexistente():
    pass


@scenario(FEATURE, "Carpeta de destino válida")
def test_carpeta_valida():
    pass


@scenario(FEATURE, "Carpeta de destino con padre inexistente")
def test_carpeta_padre_inexistente():
    pass


# ---------------------------------------------------------------------------
# Givens
# ---------------------------------------------------------------------------

@given(parsers.parse('que existe un archivo "{path}" con contenido "{contenido}"'))
def step_crear_archivo(ctx, path, contenido):
    with open(path, "w") as f:
        f.write(contenido)
    ctx["path"] = path


@given(parsers.parse('que no existe el archivo "{path}"'))
def step_no_existe_archivo(ctx, path):
    if os.path.exists(path):
        os.remove(path)
    ctx["path"] = path


@given(parsers.parse('que existe la carpeta "{path}"'))
def step_crear_carpeta(ctx, path):
    os.makedirs(path, exist_ok=True)
    ctx["path"] = path


# ---------------------------------------------------------------------------
# Whens
# ---------------------------------------------------------------------------

@when(parsers.parse('valido el host "{host}"'))
def step_validar_host(ctx, host):
    try:
        HostValidation.validate(host)
        ctx["error"] = None
    except ValueError as e:
        ctx["error"] = str(e)


@when(parsers.parse("valido el puerto {puerto:d}"))
def step_validar_puerto(ctx, puerto):
    try:
        PortValidation.validate(puerto)
        ctx["error"] = None
    except ValueError as e:
        ctx["error"] = str(e)


@when(parsers.re(r'valido el nombre "(?P<nombre>[^"]*)"'))
def step_validar_nombre(ctx, nombre):
    try:
        NameValidation.validate(nombre)
        ctx["error"] = None
    except ValueError as e:
        ctx["error"] = str(e)


@when(parsers.parse('valido el protocolo "{protocolo}"'))
def step_validar_protocolo(ctx, protocolo):
    try:
        ProtocolValidation.validate(protocolo)
        ctx["error"] = None
    except ValueError as e:
        ctx["error"] = str(e)


@when(parsers.parse('valido el archivo "{path}"'))
def step_validar_archivo(ctx, path):
    try:
        FileValidation.validate(ctx.get("path", path))
        ctx["error"] = None
    except ValueError as e:
        ctx["error"] = str(e)


@when(parsers.parse('valido la carpeta "{path}"'))
def step_validar_carpeta(ctx, path):
    try:
        FolderValidation.validate(ctx.get("path", path))
        ctx["error"] = None
    except ValueError as e:
        ctx["error"] = str(e)


# ---------------------------------------------------------------------------
# Thens
# ---------------------------------------------------------------------------

@then("la validación pasa sin error")
def step_sin_error(ctx):
    assert ctx["error"] is None, f"Error inesperado: {ctx['error']}"


@then(parsers.parse('la validación falla con el error "{mensaje}"'))
def step_con_error(ctx, mensaje):
    assert ctx["error"] is not None, "Se esperaba un error pero no ocurrió"
    assert mensaje in ctx["error"], f"Se esperaba '{mensaje}' en '{ctx['error']}'"
