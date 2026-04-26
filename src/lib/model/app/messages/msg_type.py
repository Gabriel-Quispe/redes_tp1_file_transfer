from model.codigos.cod_msj import CodMsj
from model.codigos.cod_op import CodOp


def peek_type(data: bytes) -> CodMsj:
    """Lee el TYPE del primer byte — antes de saber qué mensaje es."""
    return CodMsj(data[0])


def peek_op(data: bytes) -> CodOp:
    """Lee el OP del segundo byte (solo para mensajes REQUEST)."""
    return CodOp(data[1])
