from typing import NamedTuple

class LineSpan(NamedTuple):
    """
    LineSpan records the positional information of a line.
    It is immutable.
    """
    start: int # start offset of a line
    end: int # end offset of a line, exclusive.
    force_newline: bool = False