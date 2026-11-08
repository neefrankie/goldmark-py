from dataclasses import dataclass, field
from typing import List, NamedTuple

class Segment(NamedTuple):
    """A Segment holds information about source positions"""
    start: int = 0 # index of a string section in the whole document
    stop: int = 0 # index of the string's end position, exclusive.
    force_newline: bool = False

    def with_start(self, v: int) -> 'Segment':
        return Segment(
            start=v,
            stop=self.stop,
            force_newline=self.force_newline
        )

    def with_stop(self, v: int) -> 'Segment':
        return Segment(
            start=self.start,
            stop=v,
            force_newline=self.force_newline
        )

    def __len__(self) -> int:
        return self.stop - self.start

    def between(self, other: 'Segment') -> 'Segment':
        if self.stop != other.stop:
            raise Exception("invalid state")
        return Segment(
            start=self.start,
            stop=other.start,
        )

    def is_empty(self) -> bool:
        return self.start >= self.stop

    
@dataclass(slots=True)
class Segments:
    values: List[Segment] = field(default_factory=list)

    def append(self, seg: Segment):
        self.values.append(seg)

    def extend(self, segs: List[Segment]):
        self.values.extend(segs)

    def __len__(self):
        return len(self.values)

    def __getitem__(self, key: int) -> Segment:
        return self.values[key]

    def __setitem__(self, key: int, value: Segment):
        self.values[key] = value

    def set_sliced(self, lo: int, hi: int): 
        self.values = self.values[lo:hi]

    def get_sliced(self, lo: int, hi: int) -> List[Segment]:
        return self.values[lo:hi]
            

    def clear(self):
        self.values.clear()
