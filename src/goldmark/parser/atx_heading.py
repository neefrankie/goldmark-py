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

from .base import (
    BlockParser,
    OpenResult,
    State,
    Context
)

class ATXHeadingParser(BlockParser):

    def trigger(self) -> str:
        return '#'

    def open(self, parent: Node, reader: Reader, pc: Context) -> OpenResult | None:
        seg = reader.peek_rest_line()

        # TODO: this is repetition.
        indent = reader.indent_width(seg.start, seg.stop)

        pos = seg.start + indent.chars # first non-space char
        # Reached EOL after indent, or indented columns larger than 3
        if reader.is_eol(pos) or indent.cols > 3:
            return None

        level = reader.count_char('#', pos)
        if level == 0 or level > 6:
            return None

        pos += level # after last #, it should have a whitespace.
        # '###Hello' is not valid. 
        if not reader.is_whitespace(pos):
            return None

        node = Heading.new(level)
        
        # There is no text like: ###\n
        if reader.is_eol(pos):
            reader.advance_to_eol()
            return OpenResult(node, State.NO_CHILDREN)
        
        # Now it should be '### whatever'
        pos += 1 # after '### '
        text_seg = reader.strip_space(pos, seg.stop) # stripped leading '###[spaces]' and trailing whitespaces.
        
        if len(text_seg) == 0:
            reader.advance_to_eol()
            return OpenResult(node, State.NO_CHILDREN)

        # TODO: Goldmark parses attributes here.
        # Leave it for future implementation.

        right_level = reader.rstrip(text_seg.start, text_seg.stop, '#')
        stop = text_seg.stop - right_level
        # The text part only has trailing '###',
        # which means the whole heading is written like '### ###'
        if text_seg.start == stop:
            reader.advance_to_eol()
            return OpenResult(node, State.NO_CHILDREN)

        # After striping trailing '#'s,
        # The text part might be like 'hello    '
        if reader.is_whitespace(stop - 1):
            right_space = reader.rstrip(text_seg.start, stop)
            stop -= right_space
        
        node.get_lines().append(Segment(
            text_seg.start,
            stop,
        ))
        reader.advance_to_eol()

        return OpenResult(node, State.NO_CHILDREN)

    def try_continue(self, node: Node, reader: Reader, pc: Context) -> State:
        return State.CLOSE

    def close(self, node: Node, reader: Reader, pc: Context):
        pass

    def can_interrupt_paragraph(self) -> bool:
        return True

    def can_accept_indented_line(self) -> bool:
        return False



