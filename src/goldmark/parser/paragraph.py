
from goldmark.ast import (
    Node
)
from goldmark.text import (
    Reader,
    Segments,
)
from goldmark.ast import (
    Paragraph,
)

from .base import (
    BlockParser,
    OpenResult,
    State,
    Context,
)

class ParagraphParser(BlockParser):
    def trigger(self) -> str:
        return ''

    def open(self, parent: Node, reader: Reader, pc: Context) -> OpenResult | None:
        start = reader.pos
        if reader.is_ahead_blank(start):
            return None

        node = Paragraph()
        node.get_lines().append(reader.peek_rest_line())
        reader.advance_to_eol()
        return OpenResult(node, State.NO_CHILDREN)

    def try_continue(self, node: Node, reader: Reader, pc: Context) -> State:
        start = reader.pos

        if reader.is_ahead_blank(start):
            return State.CLOSE

        node.get_lines().append(reader.peek_rest_line())
        reader.advance_to_eol()

        return State.CONTINUE | State.NO_CHILDREN

    def close(self, node: Node, reader: Reader, pc: Context) -> None:
        lines = [
            reader.lstrip_space(line)
            for line in node.get_lines().values
        ]

        if lines:
            last_seg = reader.rstrip_space(lines[-1])
            lines[-1] = last_seg
            node.set_lines(Segments(lines))

        if not lines:
            parent = node.get_parent()
            if parent is not None:
                parent.remove_child(node)

    def can_interrupt_paragraph(self) -> bool:
        return False

    def can_accept_indented_line(self) -> bool:
        return False
        
            