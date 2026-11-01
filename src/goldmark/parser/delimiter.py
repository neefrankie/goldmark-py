from dataclasses import dataclass

from goldmark.text import (
    Segment
)

@dataclass(slots=True)
class Delimiter:
    segment: Segment
    can_open: bool
    can_close: bool
    length: int
    original_length: int
    char: str
    previous_delimiter: 'Delimiter'
    next_delimiter: 'Delimiter'