from dataclasses import dataclass, field
from typing import Any, Dict, List, NamedTuple

from .base import (
    BlockParser,
    InlineParser,
)

class WeightedBlockParser(NamedTuple):
    parser: BlockParser
    priority: int

class WeightedInlineParser(NamedTuple):
    parser: InlineParser
    priority: int


@dataclass(slots=True)
class Config:
    options: Dict[str, Any] = field(default_factory=dict)

    block_parsers: List[WeightedBlockParser] = field(default_factory=list)
    inline_parsers: List[WeightedInlineParser] = field(default_factory=list)

    paragraph_transformers: List[WeightedBlockParser] = field(default_factory=list)
    ast_transformers: List[WeightedInlineParser] = field(default_factory=list)

    escaped_space: bool = False


    def with_attribute(self):
        self.options["attribute"] = True
        return self

    def with_block_parsers(self, parsers: List[WeightedBlockParser]):
        self.block_parsers.extend(parsers)
        return self

    def with_inline_parsers(self, parsers: List[WeightedInlineParser]):
        self.inline_parsers.extend(parsers)
        return self

    def with_escaped_space(self):
        self.escaped_space = True
        return self

    def with_option(self, key: str, value: Any):
        self.options[key] = value
        return self

    def sort_block_parsers(self):
        self.block_parsers.sort(key=lambda x: x.priority)

    def sort_inline_parsers(self):
        self.inline_parsers.sort(key=lambda x: x.priority)
