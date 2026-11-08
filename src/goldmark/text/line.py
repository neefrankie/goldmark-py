from dataclasses import dataclass, field
from typing import List, NamedTuple

class GapAmount(NamedTuple):
    """
    GapAmount records the gap between two chars.

    Attributes:
        cols: number of columns between two chars.
        chars: number of chars between two chars.
    """
    cols: int = 0
    chars: int = 0

class ViewportPos(NamedTuple):
    """
    ViewportCursor records the cursor position in a viewport.
    """
    char_index: int
    column: int

@dataclass(frozen=True, slots=True)
class ViewportRange:
    start: ViewportPos
    end: ViewportPos

    @property
    def char_len(self) -> int:
        return self.end.char_index - self.start.char_index

    @property
    def col_len(self) -> int:
        return self.end.column - self.start.column
    
@dataclass(frozen=True, slots=True)
class LineContext:
    """
    LineSpan records the positional information of a line.
    It is immutable.

    Attributes:
        start: start char offset of a line in a document.
        end: end char offset of a line, exclusive.
        cols: Mapping char index to column number. This is constrained to current line. So it is relative.

    About cols
    The index in the cols list is the index of each character in the line, 
    starting from the first character of current line.
    The value is the column number corresponding the character.

    Suppose you have a line: 
    "hello\tworld\n"
     012345 678901

    The `\t` takes up 3 colums on screen.
    We use arrow to represent the columns tab takes:

    01234567890123  <- column number
    hello→→→world\n
    012345  678901  <- char index

    The cols will have value:
    
    [0, 1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 13]
    """
    start: int # start offset of a line
    end: int # end offset of a line, exclusive.
    cols: List[int] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"LineContext(start={self.start}, end={self.end}, cols={len(self.cols
        )})"

    def __getitem__(self, char_idx: int) -> int:
        """
        Returns the column offset at a char index.
        """
        return self.cols[char_idx-self.start]

    def __len__(self) -> int:
        return self.end - self.start

    def viewport_pos(self, char_idx: int) -> ViewportPos:
        return ViewportPos(char_idx, self[char_idx])

    def contains(self, char_idx: int) -> bool:
        return self.start <= char_idx < self.end

    def calc_gap(self, start_char: int, stop_char: int) -> GapAmount:
        """
        Find the gap between two chars.

        Args:
            start_char (int): start char index.
            stop_char (int): stop char index, exclusive.

        Returns:
            GapAmount: The gap between two chars.
        """
        return GapAmount(
            cols=self[stop_char] - self[start_char],
            chars=stop_char - start_char
        )



@dataclass(frozen=True, slots=True)
class Coordinate:
    row: int
    char_index: int
    line_context: LineContext

    @property
    def column(self) -> int:
        return self.line_context[self.char_index]
    

