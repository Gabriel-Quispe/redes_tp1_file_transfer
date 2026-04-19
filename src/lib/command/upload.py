import socket

from app.msj_serializer import MessageSerializer
from app.rdt.stop_and_wait import StopAndWait
from app.request.upload import RequestUpload
from cli.upload import UploadCLI
from params.upload import UploadParams


class UploadCommand:
    def execute(self):
        args = UploadCLI().args()
        params = UploadParams(args)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", 0))

        rdt = StopAndWait(sock, (params.host, params.port))
        serializer = MessageSerializer()

        RequestUpload(rdt, serializer, params.src).ejecutar()
