from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from goldmark.text import Segment, Reader

from goldmark.ast import (
    Node,
    NodeKind,
    BaseInline
)

class DelimiterProcessor(ABC):
    @abstractmethod
    def is_delimiter(self, ch: str) -> bool:
        pass

    @abstractmethod
    def can_open_closer(self, opener: Delimiter, closer: Delimiter) -> bool:
        pass

    @abstractmethod
    def on_match(self, consumes: int) -> Node:
        pass

@dataclass(slots=True, kw_only=True)
class Delimiter(BaseInline):
    segment: Segment
    can_open: bool
    can_close: bool
    length: int
    original_length: int
    char: str
    previous_delimiter: Optional['Delimiter']
    next_delimiter: Optional['Delimiter']
    processor: DelimiterProcessor

    @classmethod
    def new(cls,
        can_open: bool,
        can_close: bool,
        length: int,
        char: str,
        processor: DelimiterProcessor
    ) -> 'Delimiter':
        return cls(
            segment=Segment(),
            can_open=can_open,
            can_close=can_close,
            length=length,
            original_length=length,
            char=char,
            previous_delimiter=None,
            next_delimiter=None,
            processor=processor,
        )

    def dump(self, reader: Reader, level: int):
        indent = '    ' * level
        print(f'{indent}Delimiter: "{reader.value(self.segment)}"\n')

    @property
    def kind(self) -> NodeKind:
        return NodeKind.DELIMITER

    def consume_characters(self, n: int):
        self.length -= n
        self.segment = self.segment.with_stop(self.segment.start + self.length)

    def calc_consumption(self, closer: 'Delimiter') -> int:
        if (self.can_close or closer.can_open) and (self.original_length + closer.original_length) % 3 == 0 and (closer.original_length % 3 != 0):
            return 0

        if self.length >= 2 and closer.length >= 2:
            return 2

        return 1




    

