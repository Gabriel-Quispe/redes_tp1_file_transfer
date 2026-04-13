from cli.base import BaseCLI


class ServerCLI(BaseCLI):

    PROG = "start-server"
    USAGE = (
        "start-server [-h] [-v | -q]"
        "[-H ADDR] [-p PORT] [-s DIRPATH]"
    )
    DESCRIPTION = "<command description>"

    def __init__(self):
        super().__init__(
            self.PROG,
            self.USAGE,
            self.DESCRIPTION
        )

    def add_arguments(self):
        self.parser.add_argument(
            "-H", "--host",
            metavar="",
            help="service IP address",
            default="0.0.0.0"
        )
        self.parser.add_argument(
            "-p", "--port",
            metavar="",
            type=int,
            help="service port",
            default=8000
        )
        self.parser.add_argument(
            "-s", "--storage",
            metavar="",
            required=True,
            help="storage dir path",
        )
