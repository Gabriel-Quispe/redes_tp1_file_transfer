class PortValidation:
<<<<<<< HEAD
    MIN_PORT = 1
    MAX_PORT = 65535

    @staticmethod
    def validate(port: int) -> None:
        if not (PortValidation.MIN_PORT <= port <= PortValidation.MAX_PORT):
            raise ValueError(
                f"Port must be between {PortValidation.MIN_PORT} and {PortValidation.MAX_PORT}"
            )
=======
    @staticmethod
    def validate(port: int):
        if not (1 <= port <= 65535):
            raise ValueError("Port must be between 1 and 65535")
>>>>>>> main
