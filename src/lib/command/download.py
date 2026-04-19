import os
import socket

from app.msj_serializer import MessageSerializer
from app.request.download import RequestDownload
from app.rdt.stop_and_wait import StopAndWait
from cli.download import DownloadCLI
from params.download import DownloadParams


class DownloadCommand:
    def execute(self):
        args = DownloadCLI().args()
        params = DownloadParams(args)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", 0))

        dest_path = os.path.join(params.dst, params.name)
        rdt = StopAndWait(sock, (params.host, params.port))
        serializer = MessageSerializer()

        RequestDownload(rdt, serializer, params.name, dest_path).ejecutar()
