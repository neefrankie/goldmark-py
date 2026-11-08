
from dataclasses import dataclass

from goldmark.ast import (
    Node
)
from goldmark.text import (
    Reader,
    Segment,
)
from goldmark.ast import (
    Text,
    FencedCodeBlock,
)

from .base import (
    BlockParser,
    OpenResult,
    State,
    Context,
)

@dataclass(slots=True)
class FenceData:
    char: str
    indent: int
    length: int
    node: Node

ctx_key = '_fenced_code_block_info_key'

class FencedCodeParser(BlockParser):

    def trigger(self) -> str:
        return '~`'

    def open(self, parent: Node, reader: Reader, pc: Context) -> OpenResult | None:
        seg = reader.peek_rest_line()
        indent = reader.indent_width(seg.start, seg.stop)

        pos = seg.start + indent.chars

        if not reader.is_backtick(pos) and not reader.is_tilde(pos):
            return None

        border_char = reader.char_at(pos)
        border_len = reader.count_char(border_char, pos)

        if border_len < 3:
            return None

        pos += border_len # after ```
        space_len = reader.skip_space_tab(pos)
        pos += space_len
        lang_start = pos
        lang_len = reader.find_code_lang(pos)
        pos += lang_len
        lang_end = pos

        info_node = Text()

        if lang_end > lang_start:
            lang = reader.get_text(lang_start, lang_end)
            if border_char == '`' and '`' in lang:
                return None
            else:
                info_node.segment =Segment(
                    start=lang_start,
                    stop=lang_end
                )

        node = FencedCodeBlock.new(info_node)

        data = FenceData(
            char=border_char,
            indent=indent.chars,
            length=border_len,
            node=node
        )

        pc.set(ctx_key, data)

        return OpenResult(
            node=node,
            state=State.NO_CHILDREN
        )

    def try_continue(self, node: Node, reader: Reader, pc: Context) -> State:
        """
        Detect closing border
        """
        

        fence_data = pc.get(ctx_key)
        if not fence_data or not isinstance(fence_data, FenceData):
            return State.CLOSE

        seg = reader.peek_rest_line()

        indent = reader.indent_width(seg.start, seg.stop)
        
        if indent.cols < 4:
            pos = seg.start + indent.chars

            border_len = reader.count_char(fence_data.char, pos)

            if border_len >= fence_data.length and reader.is_ahead_blank(pos + border_len):
                reader.advance_to_eol()
                return State.CLOSE

        seg = Segment(
            start=seg.start + indent.chars,
            stop=reader.line_end,
            force_newline=True
        )

        node.get_lines().append(seg)
        reader.advance_to_eol()
        return State.CONTINUE | State.NO_CHILDREN

    def close(self, node: Node, reader: Reader, pc: Context) -> None:
        """
        Close the node
        """
        fence_data = pc.get(ctx_key)
        if fence_data is node:
            pc.set(ctx_key, None)


    def can_interrupt_paragraph(self) -> bool:
        return True

    def can_accept_indented_line(self) -> bool:
        return False

        


        

        

        