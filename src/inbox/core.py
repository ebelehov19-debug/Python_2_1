from collections.abc import Sequence, Iterable

from src.contracts.task import Task
from src.contracts.task_source import TaskSource


class TaskProcessor:
    def __init__(self, sources: Sequence[TaskSource] = None):
        self._sources = sources or []

    def iter_task(self) -> Iterable[Task]:
        for src in self._sources:
            if not isinstance(src, TaskSource):
                raise TypeError("Source object must be TaskSource")
            for message in src.fetch():
                yield message
