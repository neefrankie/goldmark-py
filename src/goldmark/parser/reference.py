from dataclasses import dataclass


@dataclass(slots=True)
class Reference:
    label: str
    destination: str
    title: str