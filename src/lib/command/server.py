from cli.server import ServerCLI
from params.server import ServerParams


class ServerCommand:
    def execute(left):
        args = ServerCLI().args()
        params = ServerParams(args)
