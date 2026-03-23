import sys
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TextIO

from src.contracts.task import Task
from src.sources.repository import register_source


def extract_task(lines: list[str], line_no: int) -> tuple[str, str]:
    try:
        return lines[0], lines[1]
    except IndexError:
        raise ValueError(
            f"Line: {line_no}. Task must contain at least 2 items, separated by ':' "
        )


@dataclass(frozen=True)
class StdinLineSource:
    stream: TextIO = sys.stdin
    name: str = "stdin"

    def fetch(self) -> Iterable[Task]:
        for line_no, line in enumerate(self.stream, start=1):
            lines = line.split(":")
            if not line.strip():
                continue
            id, payload = extract_task(lines, line_no)
            yield Task(id=id, payload=payload)


@register_source("stdin")
def create_source() -> StdinLineSource:
    return StdinLineSource()