from dataclasses import dataclass
from typing import Any, Dict, List

from goldmark.ast import (
    Node,
    merge_or_replace_text_segment
)
from goldmark.text import (
    GapAmount,
)

from .ids import IDs
from .base import (
    Context,
    Reference,
    BlockFrame,
)
from .delimiter import Delimiter


class ParseContext(Context):

    def __init__(self, *, ids: IDs | None = None):
        
        self.store: Dict[str, Any] = {}
        self._refs: Dict[str, Reference] = {}
        self._ids = ids or IDs()
        self._frame_stack: List[BlockFrame] = []

        self._block_offset: int = -1
        self._block_indent: int = -1

        self._delimiters: Delimiter | None = None
        self._last_delimiter: Delimiter | None = None

    def get(self, key: str) -> Any:
        return self.store.get(key, None)

    def set(self, key: str, value: Any):
        self.store[key] = value

    @property
    def ids(self) -> IDs:
        return self._ids

    @property
    def block_offset(self) -> int:
        return self._block_offset

    def set_block_offset(self, v: int):
        self._block_offset = v

    @property
    def block_indent(self) -> int:
        return self._block_indent

    def set_block_indent(self, v: int):
        self._block_indent = v

    @property
    def first_delimiter(self) -> Delimiter | None:
        return self._delimiters
    
    @property
    def last_delimiter(self) -> Delimiter | None:
        return self._last_delimiter

    

    def push_delimiter(self, delimiter: Delimiter):
        if self._delimiters is None:
            self._delimiters = delimiter
            self._last_delimiter = delimiter
        else:
            last = self._last_delimiter
            assert last is not None
            last.next_delimiter = delimiter
            self._last_delimiter = delimiter
            delimiter.previous_delimiter = last

    def remove_delimiter(self, delimiter: Delimiter):
        if delimiter.previous_delimiter is None: # first one
            self._delimiters = delimiter.next_delimiter
        else:
            delimiter.previous_delimiter.next_delimiter = delimiter.next_delimiter
            if delimiter.next_delimiter is not None:
                delimiter.next_delimiter.previous_delimiter = delimiter.previous_delimiter

        if delimiter.next_delimiter is None: # last one
            self._last_delimiter = delimiter.previous_delimiter

        if self._delimiters is not None:
            self._delimiters.previous_delimiter = None

        if self._last_delimiter is not None:
            self._last_delimiter.next_delimiter = None

        delimiter.next_delimiter = None
        delimiter.previous_delimiter = None

        if delimiter.length != 0:
            parent = delimiter.parent
            if parent is not None:
                merge_or_replace_text_segment(parent, delimiter, delimiter.segment)
        else:
            parent = delimiter.parent
            if parent is not None:
                parent.remove_child(delimiter)

    def clear_delimiters(self, bottom: Node):
        if self.last_delimiter is None:
            return

        c = self.last_delimiter
        while c is not None and c is not bottom:
            prev = c.get_previous_sibling()
            if isinstance(c, Delimiter):
                self.remove_delimiter(c)

            c = prev

    def add_reference(self, ref: Reference):
        key = ref.label
        if key not in self._refs:
            self._refs[key] = ref

    def get_reference(self, key: str) -> Reference | None:
        return self._refs.get(key, None)

    def list_references(self) -> List[Reference]:
        return list(self._refs.values())

    @property
    def opened_blocks(self) -> List[BlockFrame]:
        return self._frame_stack

    def set_opened_blocks(self, v: List[BlockFrame]):
        self._frame_stack = v

    def push_frame(self, frame: BlockFrame):
        self._frame_stack.append(frame)

    def pop_frame(self) -> BlockFrame | None:
        if not self._frame_stack:
            return None
        return self._frame_stack.pop()

    def remove_frames(self, start_idx: int, to_idx: int):
        if to_idx == len(self.opened_blocks) - 1:
            self._frame_stack = self._frame_stack[:start_idx]
        else:
            self._frame_stack = self._frame_stack[:start_idx] + self._frame_stack[to_idx+1:]

    @property
    def last_opened_block(self) -> BlockFrame | None:
        if not self._frame_stack:
            return None
        return self._frame_stack[-1]

    @property
    def is_in_link_label(self) -> bool:
        return 'link_label_state' in self.store




