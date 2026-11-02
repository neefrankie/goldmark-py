import re
import string
from typing import Final, List, NamedTuple

from goldmark.util import is_alnum, is_url_body

from .line import LineSpan
from .segment import Segment

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

    _EMAIL_CHARS: Final = frozenset(string.ascii_letters + string.digits + "!#$%&'*+-./=?^_`{|}~") # string.punctuation exludes (),:;<>@[\], add `.
    _SCHEME_REST: Final = frozenset(string.ascii_letters + string.digits + '.+-')
    

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

    def peek_rest_line(self, force_newline: bool = False) -> Segment | None:
        if self._line_span is None:
            return None

        return Segment(
            start=self._cursor,
            stop=self._line_span.end,
            force_newline=force_newline,
        )

    @property
    def col_offset(self) -> int:
        if self._line_span is None:
            return -1

        return self._cursor - self._line_span.start

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

    # def advance(self, n: int):
    #     self._line_offset = -1

    #     if n <= 0: # Ensure monotonic increase.
    #         return

    #     new_pos = self._cursor + n

    #     while new_pos >= self._next_line_start:
    #         self.advance_line()

    #     self._cursor = new_pos

    def advance_to_pos(self, pos: int):
        """
        Move cursor forward to the specified position.
        
        Parameter:
            pos: aboslute index in the whole document.

        NOTE
        This differs from the original implementation.
        The original implementation move n steps forward
        because most of the time it performed operation
        on a slice of string.
        Here we performa all operation on the original string,
        so using asobulute position is more convenient.
        """
        if pos >= self._length:
            raise Exception('Cursor.advance_pos: newpos is out of range')

        if pos < self._cursor:
            # Ensure monotony
            raise Exception('Cursor.advance_pos: newpos is less than current pos')

        if pos == self._cursor:
            return

        while pos >= self._next_line_start:
            self.advance_line()

        self._cursor = pos

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

    def indent(self, start: int) -> int:
        i = start
        while i < self._length:
            if self._src[i] in self._SPACE_TAB:
                i += 1
            else:
                break

        return i

    def indent_cols(self, start: int, max_cols: int) -> int:
        i = start
        cols = 0
        while i < self._length and cols < max_cols:
            if self._src[i] in self._SPACE_TAB:
                cols += 1
                i += 1
            else:
                break

        return i

    def is_space_char(self, pos: int) -> bool:
        if pos >= self._length:
            return False

        return self._src[pos] == ' '

    def is_space_tab(self, pos: int) -> bool:
        if pos >= self._length:
            return False

        return self._src[pos] in self._SPACE_TAB

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

    def ltrim_space_tab(self, seg: Segment, max_cols: int) -> Segment:
        i = seg.start
        limit = min(seg.start + max_cols, seg.stop)
        while i < limit:
            ch = self._src[i]
            if ch not in self._SPACE_TAB:
                break

            i += 1

        return seg.with_start(i)

    # === Blankline ===

    def is_blank_span(self, start: int, end: int) -> bool:
        while start < end:
            c = self._src[start]
            if c in self._SPACE_TAB:
                start += 1
            elif c == '\n':
                return True
            else:
                return False # non-space

        return False # EOF without newline.

    def is_blank(self, seg: Segment) -> bool:
        return self.is_blank_span(seg.start, seg.stop)

    def skip_blank_lines(self):
        while self._line_span:
            if self.is_blank_span(self._line_span.start, self._line_span.end):
                self.advance_line()
            else:
                break

    def is_right_angle(self, pos: int) -> bool:
        return self._src[pos] == '>'

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

    def find_email_index(self, start: int, stop: int) -> int:

        i = start
        while i < stop:
            ch = self._src[i]
            if ch not in self._EMAIL_CHARS:
                break
            i += 1

        if i == start:
            return -1

        if i >= stop or self._src[i] != '@':
            return -1

        i += 1 # eat @

        domain_start = i

        i = self._is_domain_label(i, stop)
        if i == -1:
            return -1

        # repeat '.<label>' pattern
        while i < stop and self._src[i] == '.':
            i += 1
            i = self._is_domain_label(i, stop)
            if i == -1:
                return -1

        if i == domain_start or (i > domain_start and self._src[i] == '.'):
            return -1

        return i

    def _is_domain_label(self, start: int, stop: int):
        """
        [a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?
        """
        if start >= stop:
            return -1

        first = self._src[start]
        if not is_alnum(first):
            return -1

        i = start+1
        length = 1

        while i < stop:
            ch = self._src[i]

            if is_alnum(ch):
                i += 1
                length += 1
                
                if length > 63:
                    return -1
                
                continue

            if ch == '-':
                i += 1
                length += 1

                if length > 63:
                    return -1

                continue

            break

        if self._src[i-1] == '-':
            return -1

        return i

    def find_url_index(self, start: int, stop: int) -> int:
        # [A-Za-z][A-Za-z0-9.+-]{1,31}:[^<>\x00-\x20]*
        i = start

        # [A-Za-z]
        if not (stop > start and self._src[start] in string.ascii_letters):
            return -1

        i += 1

        # [A-Za-z0-9.+-]{1,31}
        while i < stop:
            ch = self._src[i]

            if ch not in self._SCHEME_REST:
                break

            i += 1

        if i == start + 1 or i > start + 33 or i >= stop:
            return - 1

        if self._src[i] != ':':
            return -1

        i += 1

        while i < stop:
            ch = self._src[i]
            if not is_url_body(ord(ch)):
                break
            i += 1

        return i





