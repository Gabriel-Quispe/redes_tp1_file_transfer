VALID_PROTOCOLS = {"stop_and_wait", "selective_repeat"}


class ProtocolValidation:
    @staticmethod
    def validate(protocol: str):
        if protocol not in VALID_PROTOCOLS:
            raise ValueError(f"Protocol must be one of: {VALID_PROTOCOLS}")
