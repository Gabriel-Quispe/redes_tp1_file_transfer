from view.cli.base import BaseCLI


class DownloadCLI(BaseCLI):
    PROG = "download"
    USAGE = "download [-h] [-v | -q] [-H ADDR] [-p PORT] [-d FILEPATH] [-n FILENAME] [-r protocol]"
    DESCRIPTION = "Download a file from the server"

    def __init__(self):
        super().__init__(self.PROG, self.USAGE, self.DESCRIPTION)

    def add_arguments(self) -> None:
        self.parser.add_argument(
            "-H", "--host", metavar="", default="127.0.0.1", help="server IP address"
        )
        self.parser.add_argument(
            "-p", "--port", metavar="", type=int, default=8000, help="server port"
        )
        self.parser.add_argument(
            "-d", "--dst", metavar="", required=True, help="destination dir path"
        )
        self.parser.add_argument("-n", "--name", metavar="", required=True, help="file name")
        self.parser.add_argument(
            "-r",
            "--protocol",
            metavar="",
            required=True,
            choices=["stop_and_wait", "selective_repeat"],
            help="error recovery protocol",
        )
