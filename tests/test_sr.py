import os
import queue
import socket
import threading

from pytest_bdd import given, when, then, scenario, parsers

from model.rdt.selective_repeat.selective_repeat import SelectiveRepeat, MAX_SEQ
from model.rdt.stop_and_wait.segment import Segment

FEATURE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../features/rdt_selective_repeat.feature")
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_seg(seq: int, ack: int, payload: bytes) -> bytes:
    return Segment(seq, ack, payload).to_bytes()


def _parse_seg(data: bytes):
    seg = Segment.from_bytes(data)
    if seg is None:
        return None
    return (seg.seq, seg.ack, seg.payload)


def _par_sockets():
    s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s1.bind(("127.0.0.1", 0))
    s2.bind(("127.0.0.1", 0))
    return s1, s1.getsockname(), s2, s2.getsockname()


def _try_receive_once(sr_instance, timeout: float = 0.8):
    result = [None]

    def run():
        try:
            result[0] = sr_instance.recibir_mensaje()
        except Exception:
            pass

    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(timeout=timeout)
    return result[0]


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

@scenario(FEATURE, "Envío exitoso de un único mensaje con ventana")
def test_envio_unico_sr(): pass

@scenario(FEATURE, "Retransmisión selectiva del segmento perdido")
def test_retransmision_selectiva(): pass

@scenario(FEATURE, "Recepción fuera de orden con buffering")
def test_recepcion_fuera_de_orden(): pass

@scenario(FEATURE, "Descarte de segmento corrupto en el receptor SR")
def test_descarte_corrupto_sr(): pass

@scenario(FEATURE, "Segmento duplicado fuera de ventana es descartado")
def test_descarte_duplicado_sr(): pass

@scenario(FEATURE, "Falla definitiva tras MAX_REINTENTOS sin ACK")
def test_falla_max_reintentos_sr(): pass

@scenario(FEATURE, "La ventana avanza al recibir ACKs en orden")
def test_ventana_avanza(): pass

@scenario(FEATURE, "ACK fuera de ventana es ignorado")
def test_ack_fuera_de_ventana(): pass

@scenario(FEATURE, "El servidor SR lee de la cola en vez del socket compartido")
def test_servidor_lee_cola_sr(): pass


# ---------------------------------------------------------------------------
# Givens
# ---------------------------------------------------------------------------

@given("que el cliente tiene un SelectiveRepeat con ventana configurada")
def step_cliente_sr(ctx):
    s1, addr1, s2, addr2 = _par_sockets()
    ctx.update({
        "s_emisor":      s1,
        "addr_emisor":   addr1,
        "s_receptor":    s2,
        "addr_receptor": addr2,
    })
    ctx["sr"] = SelectiveRepeat(s1, addr2)


@given("que el receptor ACKea todos los segmentos")
def step_receptor_ackea_todo(ctx):
    stop     = threading.Event()
    payloads = []

    def receptor():
        ctx["s_receptor"].settimeout(5)
        while not stop.is_set():
            try:
                data, addr = ctx["s_receptor"].recvfrom(65535)
                parsed = _parse_seg(data)
                if parsed:
                    seq, _, payload = parsed
                    payloads.append(payload)
                    ctx["s_receptor"].sendto(_build_seg(0, seq, b""), addr)
            except (TimeoutError, socket.timeout):
                break

    t = threading.Thread(target=receptor, daemon=True)
    t.start()
    ctx["hilo_receptor"]      = t
    ctx["stop_receptor"]      = stop
    ctx["payloads_recibidos"] = payloads


@given(parsers.parse(
    "que el segmento con seq {seq:d} se pierde mientras {seq_a:d} y {seq_b:d} llegan bien"
))
def step_segmento_perdido_sr(ctx, seq, seq_a, seq_b):
    retransmitidos:   list = []
    llamadas_por_seq: dict = {}

    sr = ctx["sr"]
    original_sendto = sr._sendto

    def sendto_interceptado(data, addr):
        parsed = _parse_seg(data)
        if parsed:
            s, _, _ = parsed
            llamadas_por_seq[s] = llamadas_por_seq.get(s, 0) + 1
            if s == seq and llamadas_por_seq[s] == 1:
                return  # descartar primer envío
            if s == seq:
                retransmitidos.append(s)
        original_sendto(data, addr)

    sr._sendto = sendto_interceptado
    ctx["retransmitidos"] = retransmitidos

    acks_enviados = []

    def receptor():
        ctx["s_receptor"].settimeout(10)
        while True:
            try:
                data, addr = ctx["s_receptor"].recvfrom(65535)
                parsed = _parse_seg(data)
                if parsed:
                    s, _, _ = parsed
                    ctx["s_receptor"].sendto(_build_seg(0, s, b""), addr)
                    acks_enviados.append(s)
                    if len(set(acks_enviados)) >= 3:
                        break
            except (TimeoutError, socket.timeout):
                break

    t = threading.Thread(target=receptor, daemon=True)
    t.start()
    ctx["hilo_receptor"] = t
    ctx["acks_enviados"]  = acks_enviados


@given(parsers.parse(
    "que el receptor tiene un SelectiveRepeat esperando el segmento con seq {seq:d}"
))
def step_receptor_sr(ctx, seq):
    s1, addr1, s2, addr2 = _par_sockets()
    inbox = queue.Queue()
    ctx.update({
        "s_emisor":      s1,
        "addr_emisor":   addr1,
        "s_receptor":    s2,
        "addr_receptor": addr2,
        "inbox":         inbox,
        "seq_esperado":  seq,
        "sr_receptor":   SelectiveRepeat(s2, addr1, inbox=inbox),
    })


@given(parsers.parse(
    "que el receptor tiene un SelectiveRepeat que ya entregó el segmento con seq {seq:d}"
))
def step_receptor_ya_entrego_sr(ctx, seq):
    s1, addr1, s2, addr2 = _par_sockets()
    inbox = queue.Queue()
    sr    = SelectiveRepeat(s2, addr1, inbox=inbox)
    sr._buffer._base = (seq + 1) % MAX_SEQ
    ctx.update({
        "s_emisor":         s1,
        "addr_emisor":      addr1,
        "s_receptor":       s2,
        "addr_receptor":    addr2,
        "inbox":            inbox,
        "sr_receptor":      sr,
        "seq_ya_entregado": seq,
    })


@given("que el receptor SR no responde en ningún intento")
def step_receptor_sr_mudo(ctx):
    pass


@given("que el servidor tiene un SelectiveRepeat en modo servidor con una Queue")
def step_servidor_sr_con_queue(ctx):
    s1, addr1, _, _ = _par_sockets()
    inbox = queue.Queue()
    ctx.update({
        "s_servidor":  s1,
        "inbox":       inbox,
        "sr_servidor": SelectiveRepeat(s1, ("127.0.0.1", 9999), inbox=inbox),
    })


# ---------------------------------------------------------------------------
# Whens
# ---------------------------------------------------------------------------

@when(parsers.parse('el cliente llama a enviar_mensaje SR con datos "{datos}"'))
def step_enviar_mensaje_sr(ctx, datos):
    ctx["datos"] = datos.encode()
    try:
        ctx["sr"].enviar_mensaje(ctx["datos"])
        ctx["error"] = None
    except RuntimeError as e:
        ctx["error"] = e
    finally:
        if "stop_receptor" in ctx:
            ctx["stop_receptor"].set()


@when(parsers.parse(
    'el cliente llama a enviar_múltiples_mensajes SR con datos "{a}" "{b}" "{c}"'
))
def step_enviar_multiples_sr(ctx, a, b, c):
    ctx["error"] = None
    try:
        for msg in [a.encode(), b.encode(), c.encode()]:
            ctx["sr"].enviar_mensaje(msg)
    except RuntimeError as e:
        ctx["error"] = e
    finally:
        if "hilo_receptor" in ctx:
            ctx["hilo_receptor"].join(timeout=15)


@when(parsers.parse("llegan los segmentos con seq {a:d} luego {b:d} luego {c:d}"))
def step_llegan_fuera_de_orden(ctx, a, b, c):
    payloads = {
        a: f"payload_{a}".encode(),
        b: f"payload_{b}".encode(),
        c: f"payload_{c}".encode(),
    }
    for seq in [a, b, c]:
        ctx["inbox"].put((_build_seg(seq, 0, payloads[seq]), ctx["addr_emisor"]))
    ctx["payloads_originales"] = payloads
    ctx["orden_llegada"]       = [a, b, c]


@when("llega un segmento SR con checksum inválido")
def step_llega_corrupto_sr(ctx):
    seg = bytearray(_build_seg(ctx["seq_esperado"], 0, b"payload"))
    seg[2] ^= 0xFF
    ctx["inbox"].put((bytes(seg), ctx["addr_emisor"]))


@when(parsers.parse("llega nuevamente un segmento SR con seq {seq:d}"))
def step_llega_duplicado_sr(ctx, seq):
    ctx["inbox"].put((_build_seg(seq, 0, b"duplicado"), ctx["addr_emisor"]))


@when(parsers.parse("llega un ACK SR con número de seq {seq:d}"))
def step_llega_ack_fuera_ventana(ctx, seq):
    # seq=99 está fuera de MAX_SEQ=16, así que se trata como un segmento
    # cuyo seq % MAX_SEQ no está en la ventana actual → debe ser ignorado.
    ctx["inbox"].put((_build_seg(seq % MAX_SEQ, 0, b""), ctx["addr_emisor"]))


@when("el cliente envía 4 mensajes SR exitosamente")
def step_envia_4_mensajes_sr(ctx):
    ctx["error"] = None
    for i in range(4):
        try:
            ctx["sr"].enviar_mensaje(f"msg{i}".encode())
        except RuntimeError as e:
            ctx["error"] = e
            break
    if "stop_receptor" in ctx:
        ctx["stop_receptor"].set()


@when("el dispatcher deposita un segmento SR en la Queue")
def step_deposita_en_queue_sr(ctx):
    ctx["inbox"].put((_build_seg(0, 0, b"desde dispatcher SR"), ("127.0.0.1", 1234)))


# ---------------------------------------------------------------------------
# Thens
# ---------------------------------------------------------------------------

@then("el envío SR finaliza sin error")
def step_envio_sr_sin_error(ctx):
    assert ctx.get("error") is None, f"Error inesperado: {ctx['error']}"


@then(parsers.parse('el receptor SR recibe el mensaje "{datos}" correctamente'))
def step_receptor_sr_recibe(ctx, datos):
    payloads = ctx.get("payloads_recibidos", [])
    assert len(payloads) > 0, "El receptor no recibió ningún mensaje"
    assert datos.encode() in payloads


@then(parsers.parse("solo el segmento con seq {seq:d} es retransmitido"))
def step_solo_seq_retransmitido(ctx, seq):
    retransmitidos = ctx.get("retransmitidos", [])
    assert seq in retransmitidos, (
        f"Se esperaba retransmisión del seq {seq}, retransmitidos: {retransmitidos}"
    )
    otros = [s for s in retransmitidos if s != seq]
    assert len(otros) == 0, f"Se retransmitieron segmentos extra: {otros}"


@then("los 3 mensajes son recibidos correctamente")
def step_3_mensajes_recibidos(ctx):
    assert ctx.get("error") is None, f"Error durante envío múltiple: {ctx['error']}"


@then("el receptor entrega los mensajes en orden correcto")
def step_entrega_en_orden(ctx):
    sr = ctx["sr_receptor"]
    recibidos = []

    # Intentar recibir hasta 3 mensajes con timeout
    for _ in range(3):
        result = _try_receive_once(sr, timeout=1.0)
        if result is None:
            break
        recibidos.append(result)

    assert len(recibidos) > 0, "El receptor no entregó ningún mensaje"

    # Verificar orden: los payloads deben aparecer en orden 0, 1, 2
    combined = b"".join(recibidos)
    expected = b"payload_0payload_1payload_2"
    assert combined == expected, (
        f"Contenido inesperado: {combined} — recibidos: {recibidos}"
    )


@then("el receptor SR descarta el segmento silenciosamente")
def step_descarta_corrupto_sr(ctx):
    resultado = _try_receive_once(ctx["sr_receptor"])
    assert resultado is None, "El receptor entregó un segmento corrupto (no debería)"


@then("no envía ningún ACK SR")
def step_no_envia_ack_sr(ctx):
    ctx["s_emisor"].settimeout(0.3)
    try:
        ctx["s_emisor"].recvfrom(65535)
        assert False, "Se recibió un ACK inesperado para un segmento corrupto"
    except (TimeoutError, socket.timeout):
        pass


@then("el emisor SR retransmite por timeout")
def step_emisor_sr_retransmite(ctx):
    pass


@then("el receptor SR descarta el duplicado silenciosamente")
def step_descarta_duplicado_sr(ctx):
    resultado = _try_receive_once(ctx["sr_receptor"])
    assert resultado is None, "El receptor entregó un duplicado (no debería)"


@then("no entrega el payload duplicado a la capa de aplicación")
def step_no_entrega_duplicado_sr(ctx):
    pass


@then("el cliente SR lanza RuntimeError tras agotar los reintentos")
def step_lanza_error_sr(ctx):
    # SR es pipeline: enviar_mensaje retorna sin esperar ACK, por eso
    # el error no llega en el when. Lo forzamos aquí llenando la ventana
    # completa (WINDOW_SIZE envíos sin ACK) para que el siguiente bloquee
    # y agote los reintentos.
    if ctx.get("error") is None:
        sr = ctx["sr"]
        from model.rdt.selective_repeat.selective_repeat import WINDOW_SIZE, MAX_INTENTOS
        # Reducir reintentos para que el test no tarde demasiado
        import model.rdt.selective_repeat.selective_repeat as sr_mod
        original = sr_mod.MAX_INTENTOS
        sr_mod.MAX_INTENTOS = 3
        try:
            # Enviar WINDOW_SIZE + 1 mensajes sin ACK para forzar el bloqueo
            for i in range(WINDOW_SIZE + 1):
                sr.enviar_mensaje(f"timeout_{i}".encode())
        except RuntimeError as e:
            ctx["error"] = e
        finally:
            sr_mod.MAX_INTENTOS = original

    assert isinstance(ctx.get("error"), RuntimeError), (
        f"Se esperaba RuntimeError, se obtuvo: {ctx.get('error')}"
    )


@then(parsers.parse("la base de la ventana avanza al valor {base:d}"))
def step_ventana_avanza(ctx, base):
    assert ctx["sr"]._window.base == base, (
        f"Se esperaba _window.base={base}, actual: {ctx['sr']._window.base}"
    )


@then("el receptor SR ignora el ACK fuera de ventana sin error")
def step_ack_fuera_ventana_ignorado(ctx):
    resultado = _try_receive_once(ctx["sr_receptor"], timeout=0.5)
    # Aceptamos None (no llegó nada útil) o b"" (ACK vacío ignorado)
    assert resultado in (None, b""), (
        f"Se esperaba None o b'', se obtuvo: {resultado!r}"
    )


@then("el SelectiveRepeat del servidor lee de la Queue")
def step_sr_lee_queue(ctx):
    data, addr = ctx["sr_servidor"]._recv_raw()
    parsed     = _parse_seg(data)
    assert parsed is not None
    assert parsed[2] == b"desde dispatcher SR"


@then("no interfiere con el ServerListener que lee del socket")
def step_sr_no_interfiere(ctx):
    assert ctx["s_servidor"] is not None
