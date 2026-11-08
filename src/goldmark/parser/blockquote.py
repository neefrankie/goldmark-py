from typing import Tuple

from goldmark.ast import (
    Node
)
from goldmark.text import (
    Reader,
)
from goldmark.ast import (
    Blockquote,
)

from .context import (
    ParseContext,
)

from .base import (
    BlockParser,
    OpenResult,
    State,
    Context
)

class BlockquoteParser(BlockParser):
    def trigger(self) -> str:
        return '>'

    def open(self, parent: Node, reader: Reader, pc: Context) -> OpenResult | None:
        if self._process(reader):
            return OpenResult(Blockquote(), State.HAS_CHILDREN)

        return None

    def try_continue(self, node: Node, reader: Reader, pc: Context) -> State:
        if self._process(reader):
            return State.CONTINUE | State.HAS_CHILDREN

        return State.CLOSE

    def close(self, node: Node, reader: Reader, pc: Context):
        pass

    def can_interrupt_paragraph(self) -> bool:
        return True

    def can_accept_indented_line(self) -> bool:
        return False

    def _process(self, reader: Reader) -> bool:
        seg = reader.peek_rest_line()

        indent = reader.indent_width(seg.start, seg.stop)

        if indent.cols < 3:
            return False

        if indent.chars >= len(seg):
            return False

        pos = seg.start + indent.chars # >
        if not reader.is_right_angle(pos):
            return False

        pos += 1 # after >

        # This line is simply '>' or '>\n'
        if pos >= seg.stop or reader.is_newline(pos):
            reader.advance_to_pos(pos)
            return True

        reader.advance_to_pos(pos) # after '>'
        # '> '
        if reader.is_space_tab(pos):
            reader.advance_to_pos(pos+1) # After '> '

        return True

