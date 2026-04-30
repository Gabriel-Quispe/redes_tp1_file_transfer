import argparse
import os
import struct
import lib.const as const
from lib.logger import *
from lib.rdt_socket import FRDTSocket

class FRDTClient:
    def __init__(self, description):
        self.parser = argparse.ArgumentParser(description=description)
        self._add_common_arguments()
        self.args = None
        self.rdt_sock:FRDTSocket = None

    def _add_common_arguments(self):
        self.parser.add_argument("-v", "--verbose", action="store_true", help="increase output verbosity")
        self.parser.add_argument("-q", "--quiet", action="store_true", help="decrease output verbosity")
        self.parser.add_argument("-H", "--host", default="10.0.0.2", help="server IP address")
        self.parser.add_argument("-p", "--port", type=int, default=const.PORT, help="server port")
        self.parser.add_argument("-n", "--name", required=True, help="file name")
        self.parser.add_argument("-r", "--protocol", type=int, choices=[1, 2], default=1, help="protocol (1: SW, 2: SR)")

    def setup(self):
        self.args = self.parser.parse_args()
        configure_logger(self.args.verbose, self.args.quiet)
        # tanto upload como download usan un file reliable data transfer protocol
        self.rdt_sock = FRDTSocket((self.args.host, self.args.port), self.args.protocol)
    def run(self):
        pass
    def show_protocol_info(self,protocol_op):
        protocol_name:str=""
        if protocol_op==const.PROTOCOL_SR:
            protocol_name:str="Selective Repeat"
        else:
            protocol_name:str="Stop n Wait"
        logger.info(protocol_name)