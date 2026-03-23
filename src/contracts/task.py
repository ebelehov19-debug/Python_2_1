from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True, slots=True)
class Task:
    """Контракт данных задачи."""
    id: str
    payload: Any
