<<<<<<< HEAD
from view.cli.base import BaseCLI


class ServerCLI(BaseCLI):
    PROG        = "start-server"
    USAGE       = "start-server [-h] [-v | -q] [-H ADDR] [-p PORT] [-s DIRPATH]"
    DESCRIPTION = "Start the file transfer server"

    def __init__(self):
        super().__init__(self.PROG, self.USAGE, self.DESCRIPTION)

    def add_arguments(self) -> None:
        self.parser.add_argument("-H", "--host",    metavar="", default="0.0.0.0", help="service IP address")
        self.parser.add_argument("-p", "--port",    metavar="", type=int, default=8000, help="service port")
        self.parser.add_argument("-s", "--storage", metavar="", required=True, help="storage dir path")
=======
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
>>>>>>> main
