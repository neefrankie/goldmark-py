from typing import Tuple

from goldmark.ast import (
    Node
)
from goldmark.text import (
    Reader,
)
from goldmark.ast import (
    CodeBlock,
)

from .context import (
    ParseContext,
    State,
)

from .parser import (
    BlockParser,
    OpenResult,
)

class CodeBlockParser(BlockParser):

    def trigger(self) -> str:
        return ''

    def open(self, parent: Node, reader: Reader, pc: ParseContext) -> OpenResult | None:
        line = reader.rest_line
        if line is None:
            return None

        new_pos = reader.indent_cols(line.start, 4)
        if new_pos == line.start or reader.is_blank_span(line.start, line.stop):
            return None

        node = CodeBlock()
        reader.advance_to_pos(new_pos)

        segment = reader.peek_rest_line(force_newline=True)
        if segment is None:
            return None

        node.get_lines().append(segment)
        reader.advance_to_eol()
        return OpenResult(node, State.NO_CHILDREN)

    def try_continue(self, node: Node, reader: Reader, pc: ParseContext) -> State:
        line = reader.peek_rest_line()
        if line is None:
            return State.CLOSE

        if reader.is_blank(line):
            node.get_lines().append(reader.ltrim_space_tab(line, 4))
            return State.CONTINUE | State.NO_CHILDREN

        new_pos = reader.indent_cols(line.start, 4)
        if new_pos == line.start:
            return State.CLOSE

        reader.advance_to_pos(new_pos)

        segment = reader.peek_rest_line(force_newline=True)
        assert segment is not None

        node.get_lines().append(segment)
        reader.advance_to_eol()

        return State.CONTINUE | State.NO_CHILDREN

    def close(self, node: Node, reader: Reader, pc: ParseContext):
        # Remove trailing blank lines
        lines = node.get_lines()
        last = len(lines) - 1
        while last >= 0:
            line = lines[last]
            if reader.is_blank(line):
                last -= 1
            else:
                break

        lines.set_sliced(0, last+1)

    def can_interrupt_paragraph(self) -> bool:
        return False

    def can_accept_indented_line(self) -> bool:
        return True

        
    
