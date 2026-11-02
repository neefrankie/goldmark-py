from dataclasses import dataclass
from enum import Enum, Flag, auto
from typing import Dict

from goldmark.text import Segment

from .ids import IDs

@dataclass(slots=True)
class Reference:
    label: str
    destination: str
    title: str

@dataclass(slots=True)
class Delimiter:
    segment: Segment
    can_open: bool
    can_close: bool
    length: int
    original_length: int
    char: str
    previous_delimiter: 'Delimiter'
    next_delimiter: 'Delimiter'

@dataclass(slots=True)
class ParseContext:
    ids: IDs
    refs: Dict[str, Reference]
    block_offset: int
    block_indent: int
    delimiters: Delimiter
    last_delimiter: Delimiter


class State(Flag):
    NONE = auto()
    CONTINUE = auto()
    CLOSE = auto()
    HAS_CHILDREN = auto()
    NO_CHILDREN = auto()
    REQUIRE_PARAGRAPH = auto()