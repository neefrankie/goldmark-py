from collections import defaultdict
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, List

from goldmark.text import (
    Reader,
)
from goldmark.ast import (
    Node,
    Document,
    Paragraph,
)

from .base import (
    InlineParser,
    BlockParser,
    Context,
    InlineCloser,
    ParagraphTransformer,
    ASTTransformer,
    State,
    BlockFrame,
)
from .config import (
    Config,
    WeightedBlockParser,
    WeightedInlineParser,
)
from .context import (
    ParseContext
)
from .code_block import (
    CodeBlockParser,
)
from .atx_heading import (
    ATXHeadingParser,
)
from .fenced_code import (
    FencedCodeParser,
)
from .blockquote import (
    BlockquoteParser,
)
from .paragraph import (
    ParagraphParser,
)


def default_config():
    return Config(
        block_parsers=[
            WeightedBlockParser(CodeBlockParser(), 500),
            WeightedBlockParser(ATXHeadingParser(), 600),
            WeightedBlockParser(FencedCodeParser(), 700),
            WeightedBlockParser(BlockquoteParser(), 800),
            WeightedBlockParser(ParagraphParser(), 1000),
        ]
    )


class OpenBlockState(Enum):
    PARA_CONTINUED = auto()
    NEW_OPENED = auto()
    NONE_OPENED = auto()


class Parser:
    def __init__(
        self,
        *,
        config: Config
    ):
        self.options: Dict[str, Any] = config.options.copy()
        self.escape_space = config.escaped_space

        self.block_parsers: Dict[str, List[BlockParser]] = defaultdict(list)

        self.free_block_parsers: List[BlockParser] = []

        self.inline_parsers: Dict[str, List[InlineParser]] = defaultdict(list)
        self.inline_closers: List[InlineCloser] = []

        self.paragraph_transformers: List[ParagraphTransformer] = []
        self.ast_transformers: List[ASTTransformer] = []

        self.configure(config)

    def configure(self, config: Config):
        config.sort_block_parsers()
        for bp in config.block_parsers:
            self.add_block_parser(bp)

        for bps in self.block_parsers.values():
            bps.extend(self.free_block_parsers)

        config.sort_inline_parsers()
        for ip in config.inline_parsers:
            self.add_inline_parser(ip)
        

    def add_block_parser(self, v: WeightedBlockParser):
        bp = v.parser
        trigger_chars = bp.trigger()

        if not trigger_chars:
            self.free_block_parsers.append(bp)
        else:
            for ch in trigger_chars:
                self.block_parsers[ch].append(bp)

    def add_inline_parser(self, v: WeightedInlineParser):
        ip = v.parser
        trigger_chars = ip.trigger()
        for ch in trigger_chars:
            self.inline_parsers[ch].append(ip)

    def parse(
        self,
        reader: Reader,
        *, 
        context: Context | None = None
    ) -> Node:
        if context is None:
            context = ParseContext()

        reader.advance_line() # initiate first line.
        root = Document()

        return root

    def parse_blocks(self, parent: Node, reader: Reader, pc: Context):
        pc.set_opened_blocks([])

        while not reader.is_eof:
            reader.skip_blank_lines()
            if reader.is_eof:
                return

            if self.open_blocks(parent, True, reader, pc) != OpenBlockState.NEW_OPENED:
                return

    def open_blocks(
        self, 
        parent: Node, 
        blankline: bool, 
        reader: Reader, 
        ctx: Context
    ) -> OpenBlockState:
        result = OpenBlockState.NONE_OPENED
        in_paragraph = False
        last_block = ctx.last_opened_block

        if last_block and last_block.node is not None:
            in_paragraph = isinstance(last_block.node, Paragraph)

        while True:
            retry = False
            bps: List[BlockParser] = []
            
            seg = reader.peek_rest_line()

            # Nothing left in this line.
            if len(seg) == 0 or reader.is_newline(seg.start):
                return self.try_continue(result, in_paragraph, last_block, reader, ctx)
            
            indent = reader.indent_width(seg.start, seg.stop)

            # TODO: if indent reached end of line.

            bps = self.free_block_parsers
            if indent.chars < len(seg):
                # The first non-space character is the trigger character.
                ch = reader.char_at(seg.start + indent.chars)
                bps = self.block_parsers[ch]
                if not bps:
                    bps = self.free_block_parsers

            if not bps:
                return self.try_continue(result, in_paragraph, last_block, reader, ctx)

            for bp in bps:
                # Check if a parse could break a paragraph.
                if in_paragraph and result == OpenBlockState.NONE_OPENED and not bp.can_interrupt_paragraph():
                    continue

                if not bp.can_accept_indented_line():
                    continue

                # Why save those values?
                last_block = ctx.last_opened_block
                last_node = last_block.node if last_block else None

                # Try a parsing rule on current segment.
                open_result = bp.open(parent, reader, ctx)
                if open_result is None:
                    continue

                node, state = open_result
                # Set the starting position of current block.
                # We set it here rather than in each parser
                # because this we are not guaranteed custom
                # extensions could properly set it.
                node.set_pos(seg.start + indent.chars)

                if State.REQUIRE_PARAGRAPH in state:
                    if last_block and last_block.node and last_block.node is parent.get_last_child():
                        last_block.close(reader, ctx)
                        ctx.pop_frame()
                        if isinstance(last_block.node, Paragraph) and self.transform_paragraph(last_block.node, reader, ctx):
                            continuable = False
                            retry = True
                            break # go to while loop

                node.set_blank_previous_lines(blankline)

                if last_node != None and last_node.get_parent() is None:
                    last_pos = len(ctx.opened_blocks) - 1
                    self.close_blocks(last_pos, last_pos, reader, ctx)

                parent.append_child(node)
                result = OpenBlockState.NEW_OPENED
                frame = BlockFrame(node, bp)
                ctx.push_frame(frame)
                
                if State.HAS_CHILDREN in state:
                    parent = node
                    retry = True

                break
                    
            if not retry:
                break

        return self.try_continue(result, in_paragraph, last_block, reader, ctx)
    
    def try_continue(
        self,
        result: OpenBlockState,
        continuable: bool,
        last_block: BlockFrame | None,
        reader: Reader,
        pc: Context,
    ) -> OpenBlockState:
        if result == OpenBlockState.NONE_OPENED and continuable and last_block and last_block.node:
            state = last_block.parser.try_continue(last_block.node, reader, pc)
            if State.CONTINUE in state:
                result = OpenBlockState.PARA_CONTINUED

        return result

    def close_blocks(
        self,
        start: int,
        upto: int,
        reader: Reader,
        ctx: Context,
    ):
        frames = ctx.opened_blocks

        i = upto
        while i >= start:
            frame = frames[i]
            node = frame.node
            if isinstance(node, Paragraph) and node.get_parent() is not None:
                self.transform_paragraph(node, reader, ctx)

            if node and node.get_parent() is not None:
                frame.close(reader, ctx)

            i -= 1

        ctx.remove_frames(start, upto)

    def transform_paragraph(
        self,
        node: Paragraph,
        reader: Reader,
        ctx: Context,
    ) -> bool:
        for pt in self.paragraph_transformers:
            pt.transform(node, reader, ctx)
            if node.get_parent() is None:
                return True

        return False

        

            

            
                


