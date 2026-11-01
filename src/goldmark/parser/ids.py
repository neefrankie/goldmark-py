from typing import Set

from goldmark.ast import (
    NodeKind
)

class IDs:
    def __init__(self):
        self.values: Set[str] = set()

    def generate(self, value: str, kind: NodeKind) -> str:
        value = value.strip()
        return value

    def put(self, value: str):
        self.values.add(value)