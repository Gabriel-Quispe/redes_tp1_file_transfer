from cli.download import DownloadCLI
from params.download import DownloadParams


class DownloadCommand:
    def execute(left):
        args = DownloadCLI().args()
        params = DownloadParams(args)
