from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List

from goldmark.text import Segment

class Comparator(ABC):
    @abstractmethod
    def __call__(self, n1: Node, n2: Node) -> int:
        pass
    

class NodeType(Enum):
    BLOCK = auto()
    INLINE = auto()
    DOCUMENT = auto()

class NodeKind(Enum):
    # Block
    DOCUMENT = auto()
    TEXT_BLOCK = auto()
    PARAGRAPH = auto()
    HEADING = auto()
    THEMATIC_BREAK = auto()
    CODE_BLOCK = auto()
    FENCED_CODE_BLOCK = auto()
    BLOCKQUOTE = auto()
    LIST = auto()
    LIST_ITEM = auto()
    HTML_BLOCK = auto()
    LINK_REFERENCE_DEFINITION = auto()
    # Inline
    TEXT = auto()
    CODE_SPAN = auto()
    EMPHASIS = auto()
    LINK = auto()
    IMAGE = auto()
    AUTO_LINK = auto()
    RAW_HTML = auto()

@dataclass(slots=True)
class Attribute:
    name: str
    value: str

class Node(ABC):

    # === BaseNode ===

    @property
    @abstractmethod
    def has_children(self) -> bool:
        pass

    @abstractmethod
    def count_children(self) -> int:
        pass

    @abstractmethod
    def get_pos(self) -> int:
        pass

    @abstractmethod
    def set_pos(self, v: int):
        pass

    @abstractmethod
    def get_next_sibling(self) -> Node | None:
        pass

    @abstractmethod
    def get_previous_sibling(self) -> Node | None:
        pass

    @abstractmethod
    def get_parent(self) -> Node | None:
        pass

    @abstractmethod
    def set_parent(self, v: Node | None):
        pass

    @abstractmethod
    def set_previous_sibling(self, v: Node | None):
        pass

    @abstractmethod
    def set_next_sibling(self, v: Node | None):
        pass

    @abstractmethod
    def get_first_child(self) -> Node | None:
        pass

    @abstractmethod
    def get_last_child(self) -> Node | None:
        pass

    @abstractmethod
    def append_child(self, child: Node):
        pass

    @abstractmethod
    def remove_child(self, child: Node):
        pass

    @abstractmethod
    def sort_children(self, comparator: Comparator):
        pass

    @abstractmethod
    def replace_child(self, old_child: Node, new_child: Node):
        pass

    @abstractmethod
    def insert_before(self, ref_child: Node | None, new_child: Node):
        pass

    @abstractmethod
    def insert_after(self, ref_child: Node, new_child: Node):
        pass

    @abstractmethod
    def owner_document() -> Document | None:
        pass

    @abstractmethod
    def set_attribute(self, name: str, value: str):
        pass

    @abstractmethod
    def get_attribute(self, name: str) -> str | None:
        pass

    @abstractmethod
    def list_attributes(self) -> List[Attribute]:
        pass

    @abstractmethod
    def remove_attributes(self):
        pass

    # === BaseBlock ===

    @property
    @abstractmethod
    def is_raw(self) -> bool:
        pass

    @property
    @abstractmethod
    def node_type(self) -> NodeType:
        pass

    @abstractmethod
    def has_blank_previous_lines(self) -> bool:
        pass

    @abstractmethod
    def set_blank_previous_lines(self, v: bool):
        pass

    @abstractmethod
    def get_lines(self) -> List[Segment]:
        pass

    @abstractmethod
    def set_lines(self, v: List[Segment]):
        pass

    # === Concreate node

    @property
    @abstractmethod
    def kind(self) -> NodeKind:
        pass

    @abstractmethod
    def dump(self, source: str, level: int):
        pass
    

    

def ensure_isolated(v: Node):
    p = v.get_parent()
    if p is not None:
        p.remove_child(v)

@dataclass(slots=True)
class Pos:
    has: bool = False
    value: int = 0

    @property
    def pos(self) -> int:
        if self.has:
            return self.value

        return -1

    def set_pos(self, v: int):
        self.has = True
        self.value = v

@dataclass(slots=True)
class BaseNode(Node, ABC):
    first_child: Node | None = None
    last_child: Node | None = None
    parent: Node | None = None
    next_sibling: Node | None = None
    prev_sibling: Node | None = None
    child_count: int = 0
    attributes: Dict[str, str] = field(default_factory=dict)
    pos: Pos = field(default_factory=Pos)


    @property
    def has_children(self) -> bool:
        return self.first_child is not None

    def count_children(self) -> int:
        return self.child_count
    
    def get_pos(self) -> int:
        return self.pos.pos

    def set_pos(self, v: int):
        return self.pos.set_pos(v)

    def get_previous_sibling(self) -> Node | None:
        return self.prev_sibling

    def get_next_sibling(self) -> Node | None:
        return self.next_sibling

    def get_parent(self) -> Node | None:
        return self.parent

    def set_parent(self, v: Node | None):
        self.parent = v
    

    def set_previous_sibling(self, v: Node | None):
        self.prev_sibling = v

    def set_next_sibling(self, v: Node | None):
        self.next_sibling = v

    def get_first_child(self) -> Node | None:
        return self.first_child

    def get_last_child(self) -> Node | None:
        return self.last_child

    def append_child(self, child: Node):
        ensure_isolated(child)
        if self.first_child is None:
            self.first_child = child
            self.set_next_sibling(None)
            self.set_previous_sibling(None)
        else:
            last = self.last_child
            # If first_child is not None, last_child must be not None.
            assert last is not None
            last.set_next_sibling(child)
            child.set_previous_sibling(last)

        child.set_parent(self)
        self.last_child = child
        self.child_count += 1

    def remove_child(self, child: Node):
        if child.get_parent() is not self:
            return

        self.child_count -= 1
        prev = child.get_previous_sibling()
        nxt = child.get_next_sibling()
        if prev is not None:
            prev.set_next_sibling(nxt)
        else:
            self.first_child = nxt
        
        if nxt is not None:
            nxt.set_previous_sibling(prev)
        else:
            self.last_child = prev

        self.set_parent(None)
        self.set_previous_sibling(None)
        self.set_next_sibling(None)


    def remove_children(self):
        child = self.first_child
        while child is not None:
            child.set_parent(None)
            child.set_previous_sibling(None)
            nxt = child.get_next_sibling()
            child.set_next_sibling(None)
            child = nxt

        self.first_child = None
        self.last_child = None
        self.child_count = 0

    def sort_children(self, comparator: Comparator):
        head: Node | None = None
        current = self.first_child
        while current is not None:
            nxt = current.get_next_sibling()
            if head is None or comparator(head, current) >= 0:
                # Bubble smallest.
                current.set_next_sibling(head)
                if head is not None:
                    head.set_previous_sibling(current)
                head = current
                head.set_previous_sibling(None)
            else:
                # Insert current between last_smallest and smallest_next.
                last_smallest = head
                smallest_next = last_smallest.get_next_sibling() if last_smallest else None
                while smallest_next is not None and comparator(smallest_next, current) < 0:
                    last_smallest = smallest_next
                    smallest_next = last_smallest.get_next_sibling()

                current.set_next_sibling(smallest_next)
                current.set_previous_sibling(last_smallest)
                if smallest_next is not None:
                    smallest_next.set_previous_sibling(current)

                last_smallest.set_next_sibling(current)

            current = nxt

        self.first_child = head
        child = self.first_child
        while child is not None:
            self.last_child = child
            child = child.get_next_sibling()

    def replace_child(self, old_child: Node, new_child: Node):
        self.insert_before(old_child, new_child)
        self.remove_child(old_child)

    def insert_before(self, ref_child: Node | None, new_child: Node):
        self.child_count += 1
        if ref_child is None:
            self.append_child(new_child)
            return

        ensure_isolated(new_child)

        if ref_child.get_parent() is self:
            c = ref_child
            prev = c.get_previous_sibling()
            if prev is not None:
                prev.set_next_sibling(new_child)
                new_child.set_previous_sibling(prev)
            else:
                self.first_child = new_child
                new_child.set_previous_sibling(None)

            new_child.set_next_sibling(c)
            c.set_previous_sibling(new_child)
            new_child.set_parent(self)

    def insert_after(self, ref_child: Node, new_child: Node):
        self.insert_before(ref_child.get_next_sibling(), new_child)


    def owner_document(self) -> Document | None:
        doc = self.get_parent()
        dp = doc

        while dp is not None:
            doc = dp
            dp = dp.get_parent()

        if doc is None:
            return None

        if not isinstance(doc, Document):
            return None

        return doc

    def set_attribute(self, name: str, value: Any):
        self.attributes[name] = value

    def get_attribute(self, name: str) -> str | None:
        return self.attributes.get(name, None)

    def list_attributes(self) -> List[Attribute]:
        return [
            Attribute(k, v)
            for k, v in self.attributes.items()
        ]

    def remove_attributes(self):
        self.attributes = {}

def dump_node(
    v: Node, 
    source: str, 
    level: int, 
    kv: Dict[str, str] | None = None, 
    cb: Callable[[int]] | None = None
):
    name = v.kind
    indent = '    ' * level
    print(f'{indent}{name} ' + '{\n')
    indent_2 = '    ' * (level + 1)
    print(f'{indent_2}Pos: {v.get_pos()}')
    if v.node_type == NodeType.BLOCK:
        text = ''.join([
            source[line.start: line.stop]
            for line in v.get_lines()
        ])
        print(f'{indent_2}RawText: "{text}"\n')
        print(f'{indent_2}HasBlankPreviousLines: {v.has_blank_previous_lines()}')

    if kv:
        for name, value in kv.items():
            print(f'{indent_2}{name}: {value}')

    if cb is not None:
        cb(level + 1)

    c = v.get_first_child()
    while c is not None:
        c.dump(source, level+1)

    print(f'{indent}' + '}\n')


class WalkStatus(Enum):
    STOP = auto()
    SKIP_CHILDREN = auto()
    CONTINUE = auto()

class Walker(ABC):
    @abstractmethod
    def walk(self, node: Node, entering: bool) -> WalkStatus:
        pass

    def __call__(self, node: Node) -> WalkStatus:
        status = self.walk(node, True)
        if status == WalkStatus.STOP:
            return WalkStatus.STOP

        if status != WalkStatus.SKIP_CHILDREN:
            child = node.get_first_child()
            while child is not None:
                st = self(child)
                if st == WalkStatus.STOP:
                    return WalkStatus.STOP
                child = child.get_next_sibling()

        status = self.walk(node, False)
        if status == WalkStatus.STOP:
            return WalkStatus.STOP

        return WalkStatus.CONTINUE

def visit(node: Node):
    yield node

    child = node.get_first_child()
    while child is not None:
        yield from visit(child)
        child = child.get_next_sibling()

    yield node

@dataclass(slots=True)
class BaseBlock(BaseNode, ABC):
    lines: List[Segment] = field(default_factory=list)
    blank_previous_lines: bool = False

    @property
    def node_type(self) -> NodeType:
        return NodeType.BLOCK

    @property
    def is_raw(self) -> bool:
        return False

    def has_blank_previous_lines(self) -> bool:
        return self.blank_previous_lines

    def set_blank_previous_lines(self, v: bool):
        self.blank_previous_lines = v

    def get_lines(self) -> List[Segment]:
        return self.lines

    def set_lines(self, v: List[Segment]):
        self.lines = v

@dataclass(slots=True)
class Document(BaseBlock):
    meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def node_type(self) -> NodeType:
        return NodeType.DOCUMENT

    def get_pos(self) -> int:
        return 0

    @property
    def kind(self) -> NodeKind:
        return NodeKind.DOCUMENT

    def owner_document(self) -> Document | None:
        return self

    def set_meta(self, meta: Dict[str, Any]):
        self.meta = meta.copy()

    def add_meta(self, key: str, value: Any):
        self.meta[key] = value