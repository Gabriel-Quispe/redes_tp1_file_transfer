from cli.base import BaseCLI


class UploadCLI(BaseCLI):
    PROG = "upload"
    USAGE = "upload [-h] [-v | -q] [-H ADDR][-p PORT] [-s FILEPATH][-n FILENAME] [-r protocol]"
    DESCRIPTION = "<command description>"

    def __init__(self):
        super().__init__(self.PROG, self.USAGE, self.DESCRIPTION)

    def add_arguments(self):
        self.parser.add_argument(
            "-H", "--host", metavar="", default="127.0.0.1", help="server IP address"
        )
        self.parser.add_argument(
            "-p", "--port", metavar="", type=int, default=8000, help="server port"
        )
        self.parser.add_argument("-s", "--src", metavar="", required=True, help="source file path")
        self.parser.add_argument("-n", "--name", metavar="", required=True, help="file name")
        self.parser.add_argument(
            "-r",
            "--protocol",
            metavar="",
            required=True,
            choices=["stop_and_wait", "go_back_n", "selective_repeat"],
            help="error recovery protocol",
        )
