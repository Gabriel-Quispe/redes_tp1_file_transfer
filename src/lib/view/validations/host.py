import ipaddress
import re


class HostValidation:
    @staticmethod
    def validate(host: str) -> None:
        try:
            ipaddress.ip_address(host)
        except ValueError as err:
            if not re.match(r"^[a-zA-Z0-9.-]+$", host):
                raise ValueError("Invalid host") from err
