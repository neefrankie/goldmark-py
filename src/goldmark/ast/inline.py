from dataclasses import dataclass, field
from enum import Enum, Flag, auto
from typing import List

from goldmark.text import (
    Segment
)
from .ast import (
    Node,
    NodeType,
    BaseNode,
    dump_node,
    NodeKind
)

@dataclass(slots=True)
class BaseInline(BaseNode):

    @property
    def node_type(self) -> NodeType:
        return NodeType.INLINE

    @property
    def is_raw(self) -> bool:
        return False

    def has_blank_previous_lines(self) -> bool:
        raise Exception('can not call with inline nodes')

    def set_blank_previous_lines(self, v: bool):
        raise Exception('can not call with inline nodes')

    def get_lines(self) -> List[Segment]:
        raise Exception('can not call with inline nodes')

    def set_lines(self, v: List[Segment]):
        raise Exception('can not call with inline nodes')

class TextKind(Flag):
    SOFT_BREAK = auto()
    HARD_BREAK = auto()
    RAW = auto()
    CODE = auto()

def text_flags_string(flags: TextKind) -> str:
    buf: List[str] = []
    if TextKind.SOFT_BREAK in flags:
        buf.append('SOFT_BREAK')
    if TextKind.HARD_BREAK in flags:
        buf.append('HARD_BREAK')
    if TextKind.RAW in flags:
        buf.append('RAW')
    if TextKind.CODE in flags:
        buf.append('CODE')

    return ', '.join(buf)

@dataclass(slots=True)
class Text(BaseInline):
    segment: Segment = field(default_factory=Segment)
    flags: TextKind = TextKind.SOFT_BREAK

    @classmethod
    def new_raw(cls, segment: Segment) -> 'Text':
        return cls(
            segment=segment,
            flags=TextKind.RAW,
        )

    @property
    def kind(self) -> NodeKind:
        return NodeKind.TEXT

    @property
    def is_raw(self) -> bool:
        return TextKind.RAW in self.flags
    
    def get_pos(self) -> int:
        return self.segment.start

    

    def dump(self, source: str, level: int):
        m = {
            'value': f'"{self.value(source)}\n"'
        }
        fs = text_flags_string(self.flags)
        if fs:
            m['flags'] = fs
        dump_node(self, source, level, m)

    def is_soft_break(self) -> bool:
        return TextKind.SOFT_BREAK in self.flags

    def set_soft_break(self, v: bool):
        if v:
            self.flags |= TextKind.SOFT_BREAK
        else:
            self.flags &= ~TextKind.SOFT_BREAK

    def set_raw(self, v: bool):
        if v:
            self.flags |= TextKind.RAW
        else:
            self.flags &= ~TextKind.RAW

    def is_hard_break(self) -> bool:
        return TextKind.HARD_BREAK in self.flags

    def set_hard_break(self, v: bool):
        if v:
            self.flags |= TextKind.HARD_BREAK
        else:
            self.flags &= ~TextKind.HARD_BREAK

    def merge(self, other: Node, source: str) -> bool:
        if not isinstance(other, Text):
            return False

        if self.segment.stop != other.segment.start or self.segment.padding != 0 or source[self.segment.stop -1] == '\n' or self.is_raw != other.is_raw:
            return False

        self.segment = Segment(
            start=self.segment.start,
            stop=other.segment.stop,
            padding=self.segment.padding,
            force_newline=self.segment.force_newline,
        )
        self.set_soft_break(other.is_soft_break())
        self.set_hard_break(other.is_hard_break())
        return True

    def value(self, source: str) -> str:
        return source[self.segment.start:self.segment.stop]

def merge_or_append_text_segment(parent: Node, seg: Segment):
    last = parent.get_last_child()
    if isinstance(last, Text) and last.segment.stop == seg.start and not last.is_soft_break():
        last.segment = last.segment.with_stop(seg.stop)
    else:
        parent.append_child(Text(segment=seg))
    
def merge_or_replace_text_segment(parent: Node, node: Node, seg: Segment):
    prev = node.get_previous_sibling()
    if isinstance(prev, Text) and prev.segment.stop == seg.start and not prev.is_soft_break():
        prev.segment = prev.segment.with_stop(seg.stop)
        parent.remove_child(node)
    else:
        parent.replace_child(node, Text(segment=seg))

@dataclass(slots=True)
class String(BaseInline):
    value: str = ''
    flags: TextKind = TextKind.SOFT_BREAK

    @classmethod
    def new(cls, v: str) -> 'String':
        return cls(
            value=v,
        )

    @property
    def is_raw(self) -> bool:
        return TextKind.RAW in self.flags

    @property
    def kind(self) -> NodeKind:
        return NodeKind.TEXT

    def get_pos(self) -> int:
        return -1

    def dump(self, source: str, level: int):
        fs = text_flags_string(self.flags)
        if fs:
            fs = f'({fs})'

        indent = '    ' * level
        print(f'{indent}String{fs}: "{self.value}"\n')

    def set_raw(self, v: bool):
        if v:
            self.flags |= TextKind.RAW
        else:
            self.flags &= ~TextKind.RAW

    def is_code(self) -> bool:
        return TextKind.CODE in self.flags

    def set_code(self, v: bool):
        if v:
            self.flags |= TextKind.CODE
        else:
            self.flags &= ~TextKind.CODE

@dataclass(slots=True)
class CodeSpan(BaseInline):

    @property
    def kind(self) -> NodeKind:
        return NodeKind.CODE_SPAN

    def dump(self, source: str, level: int):
        dump_node(self, source, level)
    
    def is_blank(self, source: str):
        child = self.get_first_child()
        while child is not None:
            if isinstance(child, Text):
                value = child.value(source)
                if len(value.strip()) != 0:
                    return False
            child = child.get_next_sibling()

        return True

@dataclass(slots=True)
class Emphasis(BaseInline):
    level: int = 0

    @property
    def kind(self) -> NodeKind:
        return NodeKind.EMPHASIS

    def dump(self, source: str, level: int):
        dump_node(self, source, level, {
            'level': f'{self.level}'
        })


class ReferenceLinkType(Enum):
    FULL = auto()
    COLLAPSED = auto()
    SHORTCUT = auto()

@dataclass(slots=True)
class ReferenceLink:
    typ: ReferenceLinkType = ReferenceLinkType.FULL
    value: str = ''

@dataclass(slots=True)
class BaseLink(BaseInline):
    destination: str = ''
    title: str = ''
    reference: ReferenceLink | None = None

@dataclass(slots=True)
class Link(BaseLink):
    
    @property
    def kind(self) -> NodeKind:
        return NodeKind.LINK

    def dump(self, source: str, level: int):
        m = {
            'destination': self.destination
        }

        if self.title:
            m['title'] = self.title

        def cb(level: int):
            indent = '    ' * level
            print(f'{indent}Reference ' + "{\n")
            indent2 = '    ' * (level + 1)
            print(f'{indent2}Type: {self.reference.typ.name}\n')
            print(f'{indent2}Value: "{self.reference.value}"\n')
            print(f'{indent}' + '}\n')

        dump_node(self, source, level, m, cb)

@dataclass(slots=True)
class Image(BaseLink):

    @classmethod
    def new(cls, link: Link) -> 'Image':
        img = cls(
            destination=link.destination,
            title=link.title,
            reference=link.reference,
        )

        child = link.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            link.remove_child(child)
            img.append_child(child)
            child = nxt

        return img
    
    @property
    def kind(self) -> NodeKind:
        return NodeKind.IMAGE

class AutoLinkKind(Enum):
    EMAIL = auto()
    URL = auto()

@dataclass(slots=True)
class AutoLink(BaseInline):
    link_kind: AutoLinkKind = AutoLinkKind.URL
    protocol: str = ''
    value: Text | None = None

    @property
    def kind(self) -> NodeKind:
        return NodeKind.AUTO_LINK

    def url(self, source: str) -> str:
        if self.protocol and self.value:
            seg = self.value.segment

            url = source[seg.start:seg.stop]

            return f'{self.protocol}://{url}'

        return ''

    def label(self, source: str):
        return source[self.value.segment.start:self.value.segment.stop]

@dataclass(slots=True)
class RawHTML(BaseInline):
    segments: List[Segment] = field(default_factory=list)

    @property
    def kind(self) -> NodeKind:
        return NodeKind.RAW_HTML

    def dump(self, source: str, level: int):
        text = [
            source[seg.start:seg.stop]
            for seg in self.segments
        ]
        
        m = {
            'raw_text': ''.join(text)
        }
        dump_node(self, source, level, m)