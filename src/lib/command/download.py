import os
import socket
import sys

from app.msj_serializer import MessageSerializer
from app.rdt.stop_and_wait import StopAndWait
from app.request.download import RequestDownload
from cli.download import DownloadCLI
from params.download import DownloadParams


def _build_rdt(protocol: str, sock, addr):
    if protocol == "stop_and_wait":
        return StopAndWait(sock, addr)
    if protocol == "selective_repeat":
        raise NotImplementedError("Selective Repeat aún no implementado")
    raise ValueError(f"Protocolo desconocido: {protocol}")


class DownloadCommand:
    def execute(self):
        try:
            args = DownloadCLI().args()
            params = DownloadParams(args)

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(("0.0.0.0", 0))

            rdt = _build_rdt(params.protocol, sock, (params.host, params.port))
            serializer = MessageSerializer()

            dest_path = os.path.join(params.dst, params.name)
            RequestDownload(rdt, serializer, params.name, dest_path).ejecutar()

        except (ValueError, FileNotFoundError, RuntimeError, NotImplementedError,
                PermissionError, OSError) as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)
