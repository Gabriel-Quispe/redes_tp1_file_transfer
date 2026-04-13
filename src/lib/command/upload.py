from cli.upload import UploadCLI
from params.upload import UploadParams


class UploadCommand:
    def execute(left):
        args = UploadCLI().args()
        params = UploadParams(args)
