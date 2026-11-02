from abc import ABC, abstractmethod
from typing import NamedTuple, Tuple

from goldmark.ast import (
    Node
)
from goldmark.text import (
    Reader,
)

from .context import (
    ParseContext,
    State,
)

class OpenResult(NamedTuple):
    node: Node
    state: State

class BlockParser(ABC):
    @abstractmethod
    def trigger(self) -> str:
        pass

    @abstractmethod
    def open(self, parent: Node, reader:  Reader, pc: ParseContext) -> OpenResult | None:
        pass

    @abstractmethod
    def try_continue(self, node: Node, reader: Reader, pc: ParseContext) -> State:
        pass

    @abstractmethod
    def can_interrupt_paragraph(self) -> bool:
        pass

    @abstractmethod
    def can_accept_indented_line(self) -> bool:
        pass

class InlineParser(ABC):
    @abstractmethod
    def trigger(self) -> str:
        pass

    @abstractmethod
    def parse(self, parent: Node, reader: Reader, pc: ParseContext) -> Node | None:
        pass