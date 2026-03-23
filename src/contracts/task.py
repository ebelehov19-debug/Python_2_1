from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True, slots=True)
class Task:
    id: str
    payload: Any
