from goldmark.ast import (
    Node
)
from goldmark.text import (
    Reader,
)
from goldmark.ast import (
    CodeBlock,
)

from .base import (
    BlockParser,
    OpenResult,
    State,
    Context,
)

class CodeBlockParser(BlockParser):

    def trigger(self) -> str:
        return ''

    def open(self, parent: Node, reader: Reader, pc: Context) -> OpenResult | None:
        seg = reader.peek_rest_line()

        indent = reader.indent_width(seg.start, seg.stop)

        pos = seg.start + indent.chars

        if reader.is_ahead_blank(pos):
            return None

        node = CodeBlock()
        reader.advance_to_pos(pos)

        segment = reader.peek_rest_line(force_newline=True)
        if segment is None:
            return None

        node.get_lines().append(segment)
        reader.advance_to_eol()
        return OpenResult(node, State.NO_CHILDREN)

    def try_continue(self, node: Node, reader: Reader, pc: Context) -> State:
        seg = reader.peek_rest_line()

        if reader.is_ahead_blank(seg.start):
            node.get_lines().append(reader.ltrim_space_tab(seg, 4))
            return State.CONTINUE | State.NO_CHILDREN

        indent = reader.indent_width(seg.start, seg.stop)
        new_pos = seg.start + indent.chars
        if new_pos == seg.start:
            return State.CLOSE

        reader.advance_to_pos(new_pos)

        segment = reader.peek_rest_line(force_newline=True)
        assert segment is not None

        node.get_lines().append(segment)
        reader.advance_to_eol()

        return State.CONTINUE | State.NO_CHILDREN

    def close(self, node: Node, reader: Reader, pc: Context):
        pass

    def can_interrupt_paragraph(self) -> bool:
        return False

    def can_accept_indented_line(self) -> bool:
        return True

        
    
