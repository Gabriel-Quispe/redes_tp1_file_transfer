import socket as s
import sys

from model.app.request.download import RequestDownload
from model.codigos.cod_protocol import CodProtocol
from model.rdt.router import RDTRouter
from view.cli.download import DownloadCLI
from view.params.download import DownloadParams

SOCKET_TIMEOUT = 2.0


class DownloadCommand:
    def execute(self) -> None:
        try:
            args = DownloadCLI().args()
            params = DownloadParams(args)
            cod = CodProtocol.from_str(params.protocol)

            with s.socket(s.AF_INET, s.SOCK_DGRAM) as sk:
                sk.bind(("0.0.0.0", 0))
                sk.settimeout(SOCKET_TIMEOUT)

                router = RDTRouter(sk, (params.host, params.port))
                router.set_protocol(cod)
                RequestDownload(
                    router,
                    params.name,
                    params.dest_path,
                    cod,
                ).ejecutar()

        except (ValueError, OSError, RuntimeError) as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)
