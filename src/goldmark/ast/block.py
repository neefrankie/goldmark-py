from dataclasses import dataclass, field
from enum import Enum, auto

from goldmark.text import (
    Segment
)
from .ast import (
    BaseBlock,
    dump_node,
    NodeKind
)


@dataclass(slots=True)
class TextBlock(BaseBlock):

    @property
    def kind(self) -> NodeKind:
        return NodeKind.TEXT_BLOCK

    def dump(self, source: str, level: int):
        dump_node(self, source, level)

    def get_pos(self) -> int:
        if not self.lines:
            return -1

        return self.lines[0].start
    

@dataclass(slots=True)
class Paragraph(BaseBlock):

    @property
    def kind(self) -> NodeKind:
        return NodeKind.PARAGRAPH

    def dump(self, source: str, level: int):
        dump_node(self, source, level)

    def get_pos(self) -> int:
        if not self.lines:
            return -1

        return self.lines[0].start


@dataclass(slots=True)
class Heading(BaseBlock):
    level: int = 0

    @property
    def kind(self) -> NodeKind:
        return NodeKind.HEADING

    def dump(self, source: str, level: int):
        dump_node(self, source, level, {
            'level': f'{self.level}'
        })

    @classmethod
    def new(cls, level: int) -> 'Heading':
        return cls(
            level=level,
        )

@dataclass(slots=True)
class ThematicBreak(BaseBlock):

    @property
    def kind(self) -> NodeKind:
        return NodeKind.THEMATIC_BREAK
    
    def dump(self, source: str, level: int):
        dump_node(self, source, level)

    

@dataclass(slots=True)
class CodeBlock(BaseBlock):

    @property
    def kind(self) -> NodeKind:
        return NodeKind.CODE_BLOCK
    
    def dump(self, source: str, level: int):
        dump_node(self, source, level)

    
    

@dataclass(slots=True)
class FencedCodeBlock(BaseBlock):
    lang: str = ''

    @property
    def kind(self) -> NodeKind:
        return NodeKind.FENCED_CODE_BLOCK

    def dump(self, source: str, level: int):
        m = {}
        dump_node(self, source, level, m)

    def language(self, source: str) -> str:
        return self.lang

    @property
    def is_raw(self) -> bool:
        return True
    

@dataclass(slots=True)
class Blockquote(BaseBlock):

    @property
    def kind(self) -> NodeKind:
        return NodeKind.BLOCKQUOTE

    def dump(self, source: str, level: int):
        dump_node(self, source, level)

    

@dataclass(slots=True)
class ListBlock(BaseBlock):
    marker: str = ''
    is_tight: bool = True
    start: int = 0

    @property
    def kind(self) -> NodeKind:
        return NodeKind.LIST

    def dump(self, source: str, level: int):
        m = {
            'ordered': f'{self.is_ordered()}',
            'marker': self.marker,
            'tight': f'{self.is_tight}'
        }
        dump_node(self, source, level, m)

    def is_ordered(self) -> bool:
        return self.marker == '.' or self.marker == ')'

    def can_continue(self, marker: str, is_ordered: bool) -> bool:
        return marker == self.marker and is_ordered == self.is_ordered()

@dataclass(slots=True)
class ListItem(BaseBlock):
    offset: int = 0

    @property
    def kind(self) -> NodeKind:
        return NodeKind.LIST_ITEM

    def dump(self, source: str, level: int):
        m = {
            'offset': f'{self.offset}'
        }
        dump_node(self, source, level, m)

    @classmethod
    def new(cls, offset: int) -> 'ListItem':
        return cls(
            offset=offset,
        )

class HTMLBlockType(Enum):
    ONE = auto()
    TWO = auto()
    THREE = auto()
    FOUR = auto()
    FIVE = auto()
    SIX = auto()
    SEVEN = auto()

@dataclass(slots=True)
class HTMLBlock(BaseBlock):
    html_type: HTMLBlockType = HTMLBlockType.ONE
    closure_line: Segment = field(default_factory=Segment)

    @classmethod
    def new(cls, typ: HTMLBlockType) -> 'HTMLBlock':
        return cls(
            html_type=typ,
        )

    @property
    def kind(self) -> NodeKind:
        return NodeKind.HTML_BLOCK

    @property
    def is_raw(self) -> bool:
        return True

    def dump(self, source: str, level: int):
        indent = '    ' * level
        print(f'{indent}HTMLBlock ' + '{\n')
        indent2 = '    ' * (level + 1)
        print(f'{indent2}Pos: {self.get_pos()}')
        text = ''.join([
            source[line.start:line.stop]
            for line in self.lines
        ])
        print(f'{indent2}RawText: "{text}"\n')
        child = self.get_first_child()
        while child:
            child.dump(source, level+1)
            child = child.get_next_sibling()

        if self.has_closure():
            cl = self.closure_line
            print(f'{indent2}Closure: "{source[cl.start:cl.stop]}"')

        print(f"{indent2}BlankPreviousLines: {self.has_blank_previous_lines()}\n")
        print(f'{indent}' + '}\n')

    def has_closure(self) -> bool:
        return self.closure_line.start >= 0

    

@dataclass(slots=True)
class LinkReferenceDefinition(BaseBlock):
    label: str = ''
    destination: str = ''
    title: str = ''

    @classmethod
    def new(cls, label: str, destination: str, title: str) -> 'LinkReferenceDefinition':
        return cls(
            label=label,
            destination=destination,
            title=title,
        )

    @property
    def kind(self) -> NodeKind:
        return NodeKind.LINK_REFERENCE_DEFINITION

    @property
    def is_raw(self) -> bool:
        return True

    def get_pos(self) -> int:
        if not self.lines:
            return -1

        return self.lines[0].start

    def dump(self, source: str, level: int):
        m = {
            'label': self.label,
            'destination': self.destination,
            'title': self.title
        }
        dump_node(self, source, level, m)

    