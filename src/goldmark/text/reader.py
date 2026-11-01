import re
from typing import List, NamedTuple

from goldmark.util import calc_tab_width

from .line import LineSpan
from .segment import Segment

class Pos(NamedTuple):
    line_num: int
    cursor: int
    line_span: LineSpan

class MatchResult(NamedTuple):
    start: int
    end: int
    captures: List[str]

class FindClosureOptions(NamedTuple):
    code_span: bool = False
    nesting: bool = False
    newline: bool = False
    advance: bool = False

class Reader:
    _WHITESPACE = ' \t\r\n'
    _SPACE_TAB = ' \t'

    def __init__(self, src: str):
        src = src.replace('\r\n', '\n')
        if src and src[-1] != '\n':
            src += '\n'

        # This is temporary solution to replace Goldmark's TrimLeftSpaceWidth.
        # That method might not be mathmatically correct.
        src = src.expandtabs(4)
        
        self._src = src
        self._length = len(src)

        self._line_num: int = -1  # current line number
        self._line_offset: int = -1 # in current line

        self._line_span: LineSpan | None = None
        self._next_line_start = 0 # next line start offset
        self._cursor = 0 # next char offset

    @property
    def source(self) -> str:
        return self._src

    @property
    def current_line(self) -> LineSpan | None:
        return self._line_span

    @property
    def rest_line(self) -> Segment | None:
        if self._line_span is None:
            return None

        return Segment(
            start=self._cursor,
            stop=self._line_span.end,
        )

    @property
    def position(self) -> Pos | None:
        if self._line_span is None:
            return None
        
        return Pos(
            line_num=self._line_num,
            cursor=self._cursor,
            line_span=self._line_span,
        )

    @property
    def is_eof(self) -> bool:
        return self._line_span is None and self._next_line_start >= self._length

    def get_text(self, start: int, end: int):
        return self._src[start:end]

    def value(self, seg: Segment) -> str:
        text = self._src[seg.start:seg.stop]
        if seg.force_newline:
            text += '\n'

        return text

    

    def advance_line(self) -> LineSpan | None:
        if self._length == 0:
            self._line_span = None
            self._next_line_start += 1
            return None

        if self._next_line_start >= self._length:
            self._line_span = None
            self._next_line_start += 1 # Is this needed? Might not. Anyway, it's safe guard.
            return None

        next_end = self._src.find('\n', self._next_line_start)
        if next_end == -1:  # Passed EOF?
            self._line_span = None
            return None

        self._line_span = LineSpan(
            start=self._next_line_start,
            end=next_end + 1,
        )

        self._cursor = self._next_line_start # global char cursor positioned to current line start.

        self._next_line_start = next_end + 1 # position ot next line start.
        self._line_num += 1 # increase line number.

        return self._line_span

    def advance(self, n: int):
        self._line_offset = -1

        if n <= 0: # Ensure monotonic increase.
            return

        new_pos = self._cursor + n

        while new_pos >= self._next_line_start:
            self.advance_line()

        self._cursor = new_pos

    def advance_to_eol(self):
        if self._line_span is None:
            return

        self._cursor = self._line_span.end

    def peek_char(self) -> str | None:
        if 0 <= self._cursor < self._length:
            return self._src[self._cursor]

        return None

    def peek_line(self) -> LineSpan | None:
        if self._next_line_start >= self._length:
            return None

        next_end = self._src.find('\n', self._next_line_start)
        if next_end == -1:
            return None

        return LineSpan(
            start=self._next_line_start,
            end=next_end + 1,
        )
    
    def preceding_character(self) -> str:
        if self._cursor <= 0:
            return ' '

        return self._src[self._cursor - 1]

    def count_char(self, ch: str, start: int) -> int:
        """Count consecutive chars"""

        i = start
        
        if self._src[i] != ch:
            return 0
        
        while i < self._length and self._src[i] == ch:
            i += 1
        
        return i - start

    def right_count_char(self, ch: str, end: int) -> int:
        
        if self._src[end] != ch:
            return 0

        i = end
        while i >= 0 and self._src[i] == ch:
            i -= 1

        return end - i

    # === Whitespace ===

    def is_space_char(self, pos: int) -> bool:
        if pos >= self._length:
            return False

        return self._src[pos] == ' '

    def is_whitespace(self, pos: int) -> bool:
        if pos >= self._length:
            return False

        return self._src[pos] in self._WHITESPACE

    def is_newline(self, pos: int) -> bool:
        if pos >= self._length:
            return False

        return self._src[pos] == '\n'

    def rstrip_space(self, seg: Segment) -> Segment:
        text = self._src[seg.start:seg.stop]
        l = len(text) - len(text.rstrip())

        return Segment(
            start=seg.start,
            stop=seg.stop-l,
        )

    def lstrip_space(self, seg: Segment) -> Segment:
        text = self._src[seg.start:seg.stop]
        l = len(text) - len(text.lstrip())
        return Segment(
            start=seg.start+l,
            stop=seg.stop,
        )

    def strip_space(self, seg: Segment) -> Segment:
        text = self._src[seg.start:seg.stop]
        original_len = len(text)
        left_space_len = original_len - len(text.lstrip())
        # Empty
        if left_space_len == original_len:
            return Segment(seg.stop, seg.stop)
        
        right_space_len = original_len - len(text.rstrip())

        # NOTE how the calculation is performed here:
        # 012345
        # ··h··\n
        # 6
        # `stop` points to the start of next line.
        # _src[seg.start:seg.stop] result is `  h  \n`
        # Right side has 3 whitespace.
        # From stop minus 3 is the exclusive end point.
        # There's no need to add or subtract one.
        return Segment(
            start=seg.start+left_space_len,
            stop=seg.stop - right_space_len
        )

    # === Blankline ===

    def is_ahead_blank(self, start: int, end: int) -> bool:
        while start < end:
            c = self._src[start]
            if c in self._SPACE_TAB:
                start += 1
            elif c == '\n':
                return True
            else:
                return False # non-space

        return False # EOF without newline.

    def is_blankline(self, line: LineSpan) -> bool:
        return self.is_ahead_blank(line.start, line.end)

    def skip_blank_lines(self):
        while self._line_span:
            if self.is_blankline(self._line_span):
                self.advance_line()
            else:
                break

    def match(self, pattern: re.Pattern[str]) -> MatchResult | None:
        if self._line_span is None:
            return None

        m = pattern.match(self._src, self._cursor, self._line_span.end)

        if m:
            return MatchResult(
                start=m.start(),
                end=m.end(),
                captures=list(m.groups()),
            )

    
    

    # === Predicate ===



