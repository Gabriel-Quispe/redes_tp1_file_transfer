import ipaddress


class HostValidation:
    @staticmethod
    def validate(host):
        try:
            ipaddress.ip_address(host)
        except ValueError:
            if not re.match(r'^[a-zA-Z0-9.-]+$', host):
                raise ValueError("Invalid host")
