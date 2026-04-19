import os
import socket

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
        args = DownloadCLI().args()
        params = DownloadParams(args)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", 0))

        dest_path = os.path.join(params.dst, params.name)
        rdt = _build_rdt(params.protocol, sock, (params.host, params.port))
        serializer = MessageSerializer()

        RequestDownload(rdt, serializer, params.name, dest_path).ejecutar()
