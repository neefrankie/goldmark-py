import re
import string
from typing import Final, List, NamedTuple

from goldmark.util import (
    is_alnum,
    is_url_body,
    calc_tab_width,
)

from .line import LineContext, GapAmount
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

    THEMATIC_BREAK_CHARS = '_-*'
    

    def __init__(self, src: str):
        src = src.replace('\r\n', '\n')
        if src and src[-1] != '\n':
            src += '\n'
        
        self._src: str = src
        self._length: int = len(src)

        # current line number.
        # Start from -1 so first line is 0.
        self._line_num: int = -1  
        self._line_ctx: LineContext = LineContext(
            start=0,
            end=0
        )

        self._next_line_start: int = 0 # next line start offset
        self._cursor: int = 0 # next char offset

    @property
    def current_line(self) -> LineContext:
        return self._line_ctx

    @property
    def pos(self) -> int:
        return self._cursor

    @property
    def is_eol_reached(self) -> bool:
        if self._cursor >= self._length:
            return True

        if len(self._line_ctx) == 0:
            # No content
            # This is not empty line which has at least a '\n'
            return True
        
        if self._src[self._cursor] == '\n':
            return True
        
        if self._cursor == self._line_ctx.end - 1:
            return True

        return False

    @property
    def line_start(self) -> int:
        return self._line_ctx.start

    @property
    def line_end(self) -> int:
        return self._line_ctx.end - 1

    @property
    def col_offset(self) -> int:
        # Column of current cursor.
        # 0 based.
        return self._cursor - self._line_ctx.start

    @property
    def line_num(self) -> int:
        # 0 based.
        return self._line_num
    
    @property
    def is_eof(self) -> bool:
        return self._next_line_start >= self._length


    @property
    def rest_line(self) -> Segment:
        return Segment(
            start=self._cursor,
            stop=self._line_ctx.end,
        )

    @property
    def line_length(self) -> int:
        return len(self._line_ctx)

    def peek_rest_line(self, force_newline: bool = False) -> Segment:
        return Segment(
            start=self._cursor,
            stop=self._line_ctx.end,
            force_newline=force_newline,
        )

    
    def value(self, seg: Segment) -> str:
        text = self._src[seg.start:seg.stop]
        if seg.force_newline:
            text += '\n'

        return text

    def get_text(self, start: int, end: int) -> str:
        return self._src[start:end]

    def map_char_to_col(self, start: int, stop: int) -> List[int]:
        """
        This is a Post-and-Fence Problem
        """
        char_count = stop - start
        # We need to collect N+1 Viewport Boundaries
        char_cols = [-1] * (char_count + 1)

        col_n = 0 # First column always starts from 0. 
        for char_idx in range(char_count): # char_idx is relative to start
            char_cols[char_idx] = col_n
            ch = self._src[start+char_idx]
            # Clalculate next column based on
            # current char's column
            if ch == '\t':
                col_n += calc_tab_width(col_n)
            else:
                col_n += 1

        char_cols[char_count] = col_n # total columns, the last post.

        return char_cols

    def advance_line(self) -> LineContext | None:
        if self._length == 0:
            return None

        if self._next_line_start >= self._length:
            self._next_line_start += 1 # Is this needed? Might not. Anyway, it's safe guard.
            return None

        next_end = self._src.find('\n', self._next_line_start)
        if next_end == -1:  # Passed EOF?
            return None

        start_idx = self._next_line_start
        stop_idx = next_end + 1
        cols = self.map_char_to_col(start_idx, stop_idx)
        
        self._line_ctx = LineContext(
            start=self._next_line_start,
            end=next_end + 1,
            cols=cols,
        )

        # global char cursor positioned to current line start.
        self._cursor = self._line_ctx.start

        # position of next line start.
        self._next_line_start = next_end + 1 
        self._line_num += 1 # increase line number.

        return self._line_ctx

    def advance_to_pos(self, pos: int):
        """
        Move cursor forward to the specified position.
        
        Parameter:
            pos: aboslute index in the whole document.

        NOTE
        This differs from the original implementation.
        The original implementation move n steps forward
        because most of the time it performs operation
        on a local slice of string.
        Here we performa all operation on the original string,
        so using absolute position is more convenient.
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
        self._cursor = self._line_ctx.end

    def peek_char(self) -> str | None:
        if 0 <= self._cursor < self._length:
            return self._src[self._cursor]

        return None

    def peek_line(self) -> LineContext | None:
        if self._next_line_start >= self._length:
            return None

        next_end = self._src.find('\n', self._next_line_start)
        if next_end == -1:
            return None

        return LineContext(
            start=self._next_line_start,
            end=next_end + 1,
        )
    
    def preceding_character(self) -> str:
        if self._cursor <= 0:
            return ' '

        return self._src[self._cursor - 1]

    def char_at(self, pos: int) -> str:
        if pos >= self._length:
            return ''
        
        return self._src[pos]

    def count_char(self, ch: str, start: int) -> int:
        """Count consecutive chars"""

        i = start
        
        if self._src[i] != ch:
            return 0
        
        while i < self._length and self._src[i] == ch:
            i += 1
        
        return i - start

    # === Whitespace ===
    def indent_width(self, start: int, stop: int) -> GapAmount:
        """
        Skip spaces from start and returns the columns and characters
        skipped.
        """
        if not self._line_ctx.contains(start):
            raise Exception(f'{start} is not withiin current line: {self._line_ctx}')
        
        i = start

        while i < stop and self._src[i] in self._SPACE_TAB:
            i += 1

        return self._line_ctx.calc_gap(start, i)

    def skip_space_tab(self, start: int) -> int:
        i = start

        while i < self._length and self._src[i] in self._SPACE_TAB:
            i += 1

        return i - start

    def rstrip_space(self, seg: Segment) -> Segment:
        text = self._src[seg.start:seg.stop]
        l = len(text) - len(text.rstrip())

        return Segment(
            start=seg.start,
            stop=seg.stop-l,
        )

    def rstrip(self, start: int, stop: int, chars: str | None = None):
        text = self._src[start:stop]
        return len(text) - len(text.rstrip(chars))

    def lstrip_space(self, seg: Segment) -> Segment:
        text = self._src[seg.start:seg.stop]
        l = len(text) - len(text.lstrip())
        return Segment(
            start=seg.start+l,
            stop=seg.stop,
        )

    


    def strip_space(self, start: int, stop: int) -> Segment:
        text = self._src[start:stop]
        original_len = len(text)
        left_space_len = original_len - len(text.lstrip())
        # If text is empty, length is equal after stripping
        if left_space_len == original_len:
            return Segment(stop, stop)
        
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
            start=start+left_space_len,
            stop=stop - right_space_len
        )

    def ltrim_space_tab(self, seg: Segment, max_cols: int | None = None) -> Segment:
        i = seg.start
        if max_cols is None:
            limit = seg.stop
        else:
            limit = min(seg.start + max_cols, seg.stop)

        while i < limit:
            ch = self._src[i]
            if ch not in self._SPACE_TAB:
                break

            i += 1

        return seg.with_start(i)


    

    

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

    def is_eol(self, pos: int) -> bool:
        # 'a line without newline'
        # '  '
        # This only occurs at the end of a file.
        if pos >= self._length:
            return True

        # 'hello\n'
        # '    \n'
        if self._src[pos] == '\n':
            return True

        if self._src[pos] == '\r':
            if pos + 1 >= self._length or self._src[pos + 1] == '\n':
                return True
        
        return False

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

    def is_ahead_blank(self, start: int) -> bool:
        pos = start
        while pos < self._length:
            c = self._src[pos]
            if c in self._SPACE_TAB:
                pos += 1
            else:
                break

        # 2. 检查停下的位置是不是已经触及了“终点”
        # 终点包括：
        # - 已经到了字符串末尾（处理了无换行符的最后一行）
        # - 刚好停在 \n 上
        # - 刚好停在 \r 上（且后面是 \n 或直接结束）
        if pos >= self._length:
            return True

        if self._src[pos] == '\n':
            return True

        if self._src[pos] == '\r':
            if pos + 1 >= self._length or self._src[pos+1] == '\n':
                return True

        return False

    def skip_blank_lines(self) -> int:
        lines = 0
        while self._next_line_start <= self._length:
            line = self._src[self._line_ctx.start:self._line_ctx.end]
            if len(line.strip()) == 0:
                lines += 1
                self.advance_line()
            else:
                return lines

        return lines


        

    def is_right_angle(self, pos: int) -> bool:
        return self._src[pos] == '>'

    def is_backtick(self, pos: int) -> bool:
        return self._src[pos] == '`'

    def is_tilde(self, pos: int) -> bool:
        return self._src[pos] == '~'

    def is_thematic_break(self, start: int, stop: int) -> bool:
        text_slice = self._src[start:stop]
        stripped = text_slice.strip()

        if len(stripped) < 3:
            return False

        marker = stripped[0]
        if marker not in self.THEMATIC_BREAK_CHARS:
            return False

        cleaned = ''.join(c for c in stripped if c not in self._SPACE_TAB)

        return len(cleaned) >= 3 and all(c == marker for c in cleaned)


    def match(self, pattern: re.Pattern[str]) -> MatchResult | None:
        if self._line_ctx is None:
            return None

        m = pattern.match(self._src, self._cursor, self._line_ctx.end)

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



    def find_code_lang(self, start: int) -> int:
        end = start

        while end < self._length and self._src[end] not in self._WHITESPACE:
            end += 1

        return end - start


