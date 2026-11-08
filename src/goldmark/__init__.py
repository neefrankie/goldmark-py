from abc import ABC, abstractmethod
from typing import List

from goldmark.parser import (
    Parser,
    Config,
    Context,
    default_config,
)
from goldmark.text import (
    Reader,
)

class Extension(ABC):
    @abstractmethod
    def extend(self, md: Markdown):
        pass


class Markdown:
    def __init__(
        self, 
        parser: Parser | None = None,
        config: Config | None = None, # configuration to parser
        extensions: List[Extension] | None = None
    ):

        if config is None:
            config = default_config()

        self._parser: Parser = parser or Parser(config=config)
        self._extensions: List[Extension] = []

        if extensions:
            self._extensions.extend(extensions)

    def convert(self, source: str, context: Context | None = None) -> str:
        reader = Reader(source)
        doc = self._parser.parse(reader, context=context)
        return  ''

    @property
    def parser(self) -> Parser:
        return self._parser

    def set_parser(self, v: Parser):
        self._parser = v

