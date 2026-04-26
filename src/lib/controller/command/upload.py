import socket as s
import sys

from model.app.request.upload import RequestUpload
from model.codigos.cod_protocol import CodProtocol
from model.rdt.router import RDTRouter
from view.cli.upload import UploadCLI
from view.params.upload import UploadParams

SOCKET_TIMEOUT = 2.0


class UploadCommand:
    def execute(self) -> None:
        try:
            args = UploadCLI().args()
            params = UploadParams(args)
            cod = CodProtocol.from_str(params.protocol)

            with s.socket(s.AF_INET, s.SOCK_DGRAM) as sk:
                sk.bind(("0.0.0.0", 0))
                sk.settimeout(SOCKET_TIMEOUT)

                router = RDTRouter(sk, (params.host, params.port))
                router.set_protocol(cod)
                RequestUpload(
                    router,
                    params.src,
                    params.name,
                    cod,
                ).ejecutar()

        except (ValueError, OSError, RuntimeError) as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)
