class PortValidation:
    MIN_PORT = 1
    MAX_PORT = 65535

    @staticmethod
    def validate(port: int) -> None:
        if not (PortValidation.MIN_PORT <= port <= PortValidation.MAX_PORT):
            raise ValueError(
                f"Port must be between {PortValidation.MIN_PORT} and {PortValidation.MAX_PORT}"
            )
