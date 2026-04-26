import argparse
from abc import ABC, abstractmethod


class BaseCLI(ABC):
    OPTIONAL_TITLE = "optional arguments"

    def __init__(self, prog: str, usage: str, description: str) -> None:
        self.parser = argparse.ArgumentParser(
            prog=prog,
            usage=usage,
            description=description,
            formatter_class=self._formatter,
        )
        self.parser._action_groups[1].title = self.OPTIONAL_TITLE
        self._add_common_arguments()
        self.add_arguments()

    def args(self, argv=None):
        return self.parser.parse_args(argv)

    @abstractmethod
    def add_arguments(self) -> None:
        pass

    def _add_common_arguments(self) -> None:
        group = self.parser.add_mutually_exclusive_group()
        group.add_argument("-v", "--verbose", action="store_true", help="increase output verbosity")
        group.add_argument("-q", "--quiet", action="store_true", help="decrease output verbosity")

    def _formatter(self, prog):
        return argparse.HelpFormatter(prog, width=100, max_help_position=40)
