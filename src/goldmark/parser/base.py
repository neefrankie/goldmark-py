from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Flag, auto
from typing import Any, List, NamedTuple

from goldmark.ast import (
    Node,
)
from goldmark.text import (
    Reader,
    GapAmount,
)

from .ids import IDs
from .delimiter import (
    Delimiter,
)

class State(Flag):
    NONE = auto()
    CONTINUE = auto()
    CLOSE = auto()
    HAS_CHILDREN = auto()
    NO_CHILDREN = auto()
    REQUIRE_PARAGRAPH = auto()

@dataclass(slots=True)
class Reference:
    label: str
    destination: str
    title: str

class OpenResult(NamedTuple):
    node: Node
    state: State

@dataclass(slots=True)
class BlockFrame:
    node: Node | None
    parser: BlockParser

    def close(self, reader: Reader, ctx: Context):
        if self.node is not None:
            self.parser.close(self.node, reader, ctx)

class Context(ABC):

    @abstractmethod
    def get(self, key: str) -> Any:
        pass

    @abstractmethod
    def set(self, key: str, value: Any):
        pass


    @abstractmethod
    def add_reference(self, ref: Reference):
        pass

    @abstractmethod
    def get_reference(self, key: str) -> Reference | None:
        pass

    @abstractmethod
    def list_references(self) -> List[Reference]:
        pass

    @property
    @abstractmethod
    def ids(self) -> IDs:
        pass

    @property
    @abstractmethod
    def block_offset(self) -> int:
        """
        Indented whitespace chars
        """
        pass

    def set_block_offset(self, v: int):
        pass

    @property
    @abstractmethod
    def block_indent(self) -> int:
        """
        Indented columns of whitespace.
        This differs from block_offset when the whispaces have tab.
        """
        pass

    @abstractmethod
    def set_block_indent(self, v: int):
        pass

    @property
    @abstractmethod
    def first_delimiter(self) -> Delimiter | None:
        pass

    @property
    @abstractmethod
    def last_delimiter(self) -> Delimiter | None:
        pass

    @abstractmethod
    def push_delimiter(self, delimiter: Delimiter):
        pass

    @abstractmethod
    def remove_delimiter(self, delimiter: Delimiter):
        pass

    @abstractmethod
    def clear_delimiters(self, bottom: Node):
        pass

    @property
    @abstractmethod
    def opened_blocks(self) -> List[BlockFrame]:
        pass

    @abstractmethod
    def set_opened_blocks(self, v: List[BlockFrame]):
        pass

    @abstractmethod
    def push_frame(self, frame: BlockFrame):
        pass

    @abstractmethod
    def pop_frame(self) -> BlockFrame | None:
        pass

    @abstractmethod
    def remove_frames(self, start_idx: int, to_idx: int):
        pass

    @property
    @abstractmethod
    def last_opened_block(self) -> BlockFrame | None:
        pass

    @property
    @abstractmethod
    def is_in_link_label(self) -> bool:
        pass


class BlockParser(ABC):
    @abstractmethod
    def trigger(self) -> str:
        pass

    @abstractmethod
    def open(self, parent: Node, reader:  Reader, pc: Context) -> OpenResult | None:
        pass

    @abstractmethod
    def try_continue(self, node: Node, reader: Reader, pc: Context) -> State:
        pass

    @abstractmethod
    def close(self, node: Node, reader: Reader, pc: Context):
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
    def parse(self, parent: Node, reader: Reader, pc: Context) -> Node | None:
        pass

class InlineCloser(ABC):
    @abstractmethod
    def close_delimiter(self, parent: Node, reader: Reader, pc: Context) -> Node | None:
        pass

class ParagraphTransformer(ABC):
    @abstractmethod
    def transform(self, node: Node, reader: Reader, pc: Context):
        pass

class ASTTransformer(ABC):
    @abstractmethod
    def transform(self, node: Node, reader: Reader, pc: Context):
        pass
        


    