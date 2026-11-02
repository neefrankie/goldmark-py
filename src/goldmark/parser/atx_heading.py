from typing import Tuple

from goldmark.ast import (
    Node
)
from goldmark.text import (
    Reader,
    Segment,
)
from goldmark.ast import (
    Heading,
)

from .context import (
    ParseContext,
    State,
)
from .parser import (
    BlockParser,
    OpenResult
)

class ATXHeadingParser(BlockParser):

    def trigger(self) -> str:
        return '#'

    def open(self, parent: Node, reader: Reader, pc: ParseContext) -> OpenResult | None:
        line = reader.rest_line
        if line is None:
            return None
        
        pos = pc.block_offset
        if pos < 0:
            return None

        level = reader.count_char('#', line.start)
        if level == 0 or level > 6:
            return None

        # ###Hello
        if not reader.is_whitespace(line.start + level):
            return None

        # ###\n
        if reader.is_newline(line.start + level):
            return OpenResult(Heading.new(level), State.NO_CHILDREN)
        
        # Now it should be '### whatever'
        text_start = line.start + level + 1 # After '### '
        text_seg = reader.strip_space(Segment(text_start, line.stop)) # stripped leading '###[spaces]' and trailing whitespaces.
        
        if len(text_seg) == 0:
            reader.advance_to_eol()
            return OpenResult(Heading.new(level), State.NO_CHILDREN)

        # TODO: Goldmark parses attributes here.
        # Leave it for future implementation.

        
        right_level = reader.right_count_char('#', text_seg.stop-1)
        # The text part only has trailing '###',
        # which means the whole heading is written like '### ###'
        if right_level == len(text_seg): 
            reader.advance_to_eol()
            return OpenResult(Heading.new(level), State.NO_CHILDREN)

        # The text part might be like 'hello    ###'
        stop = text_seg.stop - right_level
        if reader.is_whitespace(stop - 1):
            text_seg = reader.rstrip_space(Segment(text_seg.start, stop))
        
        node = Heading.new(level)
        node.get_lines().append(text_seg)
        reader.advance_to_eol()

        return OpenResult(node, State.NO_CHILDREN)

    def try_continue(self, node: Node, reader: Reader, pc: ParseContext) -> State:
        return State.CLOSE

    def close(self, node: Node, reader: Reader, pc: ParseContext):
        pass

    def can_interrupt_paragraph(self) -> bool:
        return True

    def can_accept_indented_line(self) -> bool:
        return False



