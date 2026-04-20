import socket
import sys

from app.msj_serializer import MessageSerializer
from app.rdt.stop_and_wait import StopAndWait
from app.request.upload import RequestUpload
from cli.upload import UploadCLI
from params.upload import UploadParams


def _build_rdt(protocol: str, sock, addr):
    if protocol == "stop_and_wait":
        return StopAndWait(sock, addr)
    if protocol == "selective_repeat":
        raise NotImplementedError("Selective Repeat aún no implementado")
    raise ValueError(f"Protocolo desconocido: {protocol}")


class UploadCommand:
    def execute(self):
        try:
            args = UploadCLI().args()
            params = UploadParams(args)

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(("0.0.0.0", 0))

            rdt = _build_rdt(params.protocol, sock, (params.host, params.port))
            serializer = MessageSerializer()

            RequestUpload(rdt, serializer, params.src, params.name).ejecutar()

        except (ValueError, FileNotFoundError, RuntimeError, NotImplementedError) as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)
