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
    State,
)

from .parser import (
    BlockParser,
    OpenResult,
)

class BoockquoteParser(BlockParser):
    def trigger(self) -> str:
        return '>'

    def open(self, parent: Node, reader: Reader, pc: ParseContext) -> OpenResult | None:
        if self._process(reader):
            return OpenResult(Blockquote(), State.HAS_CHILDREN)

        return None

    def try_continue(self, node: Node, reader: Reader, pc: ParseContext) -> State:
        if self._process(reader):
            return State.CONTINUE | State.HAS_CHILDREN

        return State.CLOSE

    def close(self, node: Node, reader: Reader, pc: ParseContext):
        pass

    def can_interrupt_paragraph(self) -> bool:
        return True

    def can_accept_indented_line(self) -> bool:
        return False

    def _process(self, reader: Reader) -> bool:
        line = reader.rest_line
        if line is None:
            return False

        new_pos = reader.indent(line.start)

        cols = new_pos - line.start

        if cols > 3 or cols >= len(line) or not reader.is_right_angle(new_pos):
            return False

        new_pos += 1 # eat '>'

        # This line is simply '>' or '>\n'
        if new_pos >= line.stop or reader.is_newline(new_pos):
            reader.advance_to_pos(new_pos)
            return True

        reader.advance_to_pos(new_pos) # after '>'
        # '> '
        if reader.is_space_tab(new_pos):
            reader.advance_to_pos(new_pos+1) # After '> '

        return True

