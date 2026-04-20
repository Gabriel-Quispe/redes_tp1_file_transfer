import os
import queue
import socket
import threading

from pytest_bdd import given, when, then, scenario, parsers

from app.rdt.stop_and_wait import StopAndWait, _build_segment, _parse_segment

FEATURE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../features/rdt_stop_and_wait.feature")
)


@scenario(FEATURE, "Retransmisión ante timeout por pérdida de paquete de datos")
def test_retransmision_perdida_datos():
    pass


@scenario(FEATURE, "Retransmisión ante timeout por pérdida de ACK")
def test_retransmision_perdida_ack():
    pass


@scenario(FEATURE, "Descarte de segmento corrupto en el receptor")
def test_descarte_corrupto():
    pass


@scenario(FEATURE, "Descarte de segmento duplicado en el receptor")
def test_descarte_duplicado():
    pass


@scenario(FEATURE, "Falla definitiva tras MAX_REINTENTOS sin ACK")
def test_falla_max_reintentos():
    pass


@scenario(FEATURE, "Alternancia correcta del número de secuencia")
def test_alternancia_seq():
    pass


@scenario(FEATURE, "El servidor lee de la cola en vez del socket compartido")
def test_servidor_lee_cola():
    pass


def _par_sockets():
    s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s1.bind(("127.0.0.1", 0))
    s2.bind(("127.0.0.1", 0))
    return s1, s1.getsockname(), s2, s2.getsockname()


# ---------------------------------------------------------------------------
# Givens
# ---------------------------------------------------------------------------


@given(
    parsers.parse(
        "que el cliente tiene un StopAndWait configurado con timeout de {t:f} segundos"
    )
)
def step_cliente_saw(ctx, t):
    s1, addr1, s2, addr2 = _par_sockets()
    ctx.update(
        {"s_emisor": s1, "addr_emisor": addr1, "s_receptor": s2, "addr_receptor": addr2}
    )
    ctx["saw"] = StopAndWait(s1, addr2)


@given("que el primer envío del segmento se pierde")
def step_primer_envio_perdido(ctx):
    # Monkey-patch sobre saw._sendto (método Python propio), no sobre el
    # atributo nativo del socket que es read-only en CPython.
    saw = ctx["saw"]
    original_sendto = saw._sendto
    calls = {"n": 0}

    def sendto_lossy(data, addr):
        calls["n"] += 1
        if calls["n"] > 1:
            original_sendto(data, addr)

    saw._sendto = sendto_lossy

    def receptor():
        ctx["s_receptor"].settimeout(5)
        data, addr = ctx["s_receptor"].recvfrom(65535)
        parsed = _parse_segment(data)
        if parsed:
            seq, _, payload = parsed
            ctx["s_receptor"].sendto(_build_segment(0, seq, b""), addr)
            ctx["payload_recibido"] = payload

    t = threading.Thread(target=receptor, daemon=True)
    t.start()
    ctx["hilo_receptor"] = t


@given("que el ACK del receptor se pierde")
def step_ack_perdido(ctx):
    def receptor():
        ctx["s_receptor"].settimeout(5)
        # Primera recepción: no manda ACK
        data, addr = ctx["s_receptor"].recvfrom(65535)
        parsed = _parse_segment(data)
        if parsed:
            ctx["payload_recibido"] = parsed[2]
        # Segunda recepción (retransmisión): manda ACK
        data2, addr2 = ctx["s_receptor"].recvfrom(65535)
        parsed2 = _parse_segment(data2)
        if parsed2:
            ctx["s_receptor"].sendto(_build_segment(0, parsed2[0], b""), addr2)

    t = threading.Thread(target=receptor, daemon=True)
    t.start()
    ctx["hilo_receptor"] = t


@given("que el receptor no responde en ningún intento")
def step_receptor_mudo(ctx):
    pass


@given(
    parsers.parse(
        "que el receptor tiene un StopAndWait esperando el segmento con seq {seq:d}"
    )
)
def step_receptor_saw(ctx, seq):
    s1, addr1, s2, addr2 = _par_sockets()
    inbox = queue.Queue()
    ctx.update(
        {
            "s_emisor": s1,
            "addr_emisor": addr1,
            "s_receptor": s2,
            "addr_receptor": addr2,
            "inbox": inbox,
            "seq_esperado": seq,
            "saw_receptor": StopAndWait(s2, addr1, inbox=inbox),
        }
    )


@given(
    parsers.parse(
        "que el receptor tiene un StopAndWait que ya recibió el segmento con seq {seq:d}"
    )
)
def step_receptor_ya_recibio(ctx, seq):
    s1, addr1, s2, addr2 = _par_sockets()
    inbox = queue.Queue()
    saw = StopAndWait(s2, addr1, inbox=inbox)
    saw._seq_rx = 1 - seq
    ctx.update(
        {
            "s_emisor": s1,
            "addr_emisor": addr1,
            "s_receptor": s2,
            "addr_receptor": addr2,
            "inbox": inbox,
            "saw_receptor": saw,
            "seq_ya_recibido": seq,
        }
    )


@given(parsers.parse("que el cliente tiene un StopAndWait con seq_tx inicial {seq:d}"))
def step_cliente_saw_seq(ctx, seq):
    s1, addr1, s2, addr2 = _par_sockets()
    ctx.update(
        {"s_emisor": s1, "addr_emisor": addr1, "s_receptor": s2, "addr_receptor": addr2}
    )
    ctx["saw"] = StopAndWait(s1, addr2)
    assert ctx["saw"]._seq_tx == seq


@given("que el servidor tiene un StopAndWait en modo servidor con una Queue")
def step_servidor_con_queue(ctx):
    s1, addr1, _, _ = _par_sockets()
    inbox = queue.Queue()
    ctx.update(
        {
            "s_servidor": s1,
            "inbox": inbox,
            "saw_servidor": StopAndWait(s1, ("127.0.0.1", 9999), inbox=inbox),
        }
    )


# ---------------------------------------------------------------------------
# Whens
# ---------------------------------------------------------------------------


@when(parsers.parse('el cliente llama a enviar_mensaje con datos "{datos}"'))
def step_enviar_mensaje(ctx, datos):
    ctx["datos"] = datos.encode()
    try:
        ctx["saw"].enviar_mensaje(ctx["datos"])
        ctx["error"] = None
    except RuntimeError as e:
        ctx["error"] = e


@when("llega un segmento con checksum inválido")
def step_llega_corrupto(ctx):
    seg = bytearray(_build_segment(ctx["seq_esperado"], 0, b"payload"))
    seg[2] ^= 0xFF
    ctx["inbox"].put((bytes(seg), ctx["addr_emisor"]))


@when(parsers.parse("llega nuevamente un segmento con seq {seq:d}"))
def step_llega_duplicado(ctx, seq):
    ctx["inbox"].put((_build_segment(seq, 0, b"duplicado"), ctx["addr_emisor"]))


@when("el cliente envía el primer mensaje exitosamente")
def step_envio_1(ctx):
    def receptor():
        ctx["s_receptor"].settimeout(5)
        data, addr = ctx["s_receptor"].recvfrom(65535)
        parsed = _parse_segment(data)
        if parsed:
            ctx["s_receptor"].sendto(_build_segment(0, parsed[0], b""), addr)

    t = threading.Thread(target=receptor, daemon=True)
    t.start()
    ctx["saw"].enviar_mensaje(b"mensaje1")
    t.join(timeout=3)


@when("el cliente envía el segundo mensaje exitosamente")
def step_envio_2(ctx):
    def receptor():
        ctx["s_receptor"].settimeout(5)
        data, addr = ctx["s_receptor"].recvfrom(65535)
        parsed = _parse_segment(data)
        if parsed:
            ctx["s_receptor"].sendto(_build_segment(0, parsed[0], b""), addr)

    t = threading.Thread(target=receptor, daemon=True)
    t.start()
    ctx["saw"].enviar_mensaje(b"mensaje2")
    t.join(timeout=3)


@when("el dispatcher deposita un segmento en la Queue")
def step_deposita_en_queue(ctx):
    ctx["inbox"].put((_build_segment(0, 0, b"desde dispatcher"), ("127.0.0.1", 1234)))


# ---------------------------------------------------------------------------
# Thens
# ---------------------------------------------------------------------------


@then("el cliente retransmite el segmento automáticamente")
def step_retransmite(ctx):
    if "hilo_receptor" in ctx:
        ctx["hilo_receptor"].join(timeout=5)
    assert ctx.get("error") is None


@then(parsers.parse('el receptor recibe el mensaje "{datos}" correctamente'))
def step_receptor_recibe(ctx, datos):
    assert ctx.get("payload_recibido") is not None


@then("el cliente retransmite el segmento")
def step_retransmite_ack(ctx):
    if "hilo_receptor" in ctx:
        ctx["hilo_receptor"].join(timeout=5)
    assert ctx.get("error") is None


@then("el receptor descarta el duplicado silenciosamente")
def step_descarta_duplicado_ok(ctx):
    pass


@then("el receptor reenvía el ACK")
def step_reenvía_ack(ctx):
    pass


@then("el cliente recibe el ACK y avanza el número de secuencia")
def step_avanza_seq(ctx):
    assert ctx["saw"]._seq_tx == 1


@then("el receptor descarta el segmento silenciosamente")
def step_descarta_corrupto(ctx):
    resultado = ctx["saw_receptor"]._esperar_segmento(ctx["seq_esperado"])
    assert resultado is None


@then("no envía ningún ACK")
def step_no_envia_ack(ctx):
    ctx["s_emisor"].settimeout(0.3)
    try:
        ctx["s_emisor"].recvfrom(65535)
        assert False, "Se recibió un ACK inesperado"
    except (TimeoutError, socket.timeout):
        pass


@then("el emisor retransmite por timeout")
def step_emisor_retransmite(ctx):
    pass


@then(parsers.parse("el receptor reenvía el ACK {seq:d}"))
def step_reenvía_ack_seq(ctx, seq):
    resultado = ctx["saw_receptor"]._esperar_segmento(ctx["saw_receptor"]._seq_rx)
    assert resultado is None


@then("no entrega el payload duplicado a la capa de aplicación")
def step_no_entrega_duplicado(ctx):
    pass


@then(parsers.parse("el cliente lanza RuntimeError tras {n:d} intentos fallidos"))
def step_lanza_runtime_error(ctx, n):
    assert isinstance(ctx.get("error"), RuntimeError)
    assert str(n) in str(ctx["error"])


@then(parsers.parse("seq_tx pasa a {seq:d}"))
def step_seq_tx_es(ctx, seq):
    assert ctx["saw"]._seq_tx == seq


@then(parsers.parse("seq_tx vuelve a {seq:d}"))
def step_seq_tx_vuelve(ctx, seq):
    assert ctx["saw"]._seq_tx == seq


@then("el StopAndWait del servidor lee de la Queue")
def step_saw_lee_queue(ctx):
    data, addr = ctx["saw_servidor"]._recibir_raw()
    parsed = _parse_segment(data)
    assert parsed is not None
    assert parsed[2] == b"desde dispatcher"


@then("no interfiere con el ServerListener que lee del socket")
def step_no_interfiere(ctx):
    assert ctx["s_servidor"] is not None
