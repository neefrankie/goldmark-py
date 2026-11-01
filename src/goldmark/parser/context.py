from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict

from .reference import Reference
from .ids import IDs
from .delimiter import Delimiter

@dataclass(slots=True)
class ParseContext:
    ids: IDs
    refs: Dict[str, Reference]
    block_offset: int
    block_indent: int
    delimiters: Delimiter
    last_delimiter: Delimiter


class State(Enum):
    NONE = auto()
    CONTINUE = auto()
    CLOSE = auto()
    HAS_CHILDREN = auto()
    NO_CHILDREN = auto()
    REQUIRE_PARAGRAPH = auto()