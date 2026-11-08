
from goldmark.ast import (
    Node,
    ThematicBreak,
)
from goldmark.text import (
    Reader,
)

from .base import (
    BlockParser,
    OpenResult,
    State,
    Context
)

class ThematicBreakParser(BlockParser):
    def trigger(self) -> str:
        return Reader.THEMATIC_BREAK_CHARS

    def open(self, parent: Node, reader: Reader, pc: Context) -> OpenResult | None:
        start_pos = reader.pos
        stop_pos = reader.line_end
        cols, chars = reader.indent_width(start_pos, stop_pos)
        if cols > 3:
            return None

        start_pos += chars

        if reader.is_thematic_break(start_pos, stop_pos):
            reader.advance_to_eol()
            return OpenResult(
                node=ThematicBreak(),
                state=State.NO_CHILDREN,
            )

        return None

    def try_continue(self, node: Node, reader: Reader, pc: Context) -> State:
        return State.CLOSE

    def close(self, node: Node, reader: Reader, pc: Context) -> None:
        pass

    def can_interrupt_paragraph(self) -> bool:
        return True

    def can_accept_indented_line(self) -> bool:
        return False