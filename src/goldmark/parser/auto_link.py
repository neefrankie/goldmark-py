from goldmark.ast import (
    Node
)
from goldmark.text import (
    Reader,
    Segment,
)
from goldmark.ast import (
    AutoLinkKind,
    Text,
    AutoLink,
)

from .base import (
    InlineParser,
    Context
)

class AutoLinkParser(InlineParser):
    def trigger(self) -> str:
        return '<'
    
    def parse(self, parent: Node, reader: Reader, pc: Context) -> Node | None:
        line = reader.rest_line
        assert line is not None
        kind = AutoLinkKind.EMAIL

        stop = reader.find_email_index(line.start+1, line.stop)
        if stop < 0:
            stop = reader.find_url_index(line.start+1, line.stop)
            kind = AutoLinkKind.URL

        if stop < 0:
            return None

        stop += 1
        if stop >= line.stop or reader.is_right_angle(stop):
            return None

        value = Text(segment=Segment(start=line.start+1, stop=stop))

        reader.advance_to_pos(stop+1)

        return AutoLink(link_kind=kind, value=value)
