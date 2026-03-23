import pytest
from src.contracts.task import Task
import pytest
from src.contracts.task import Task
from src.contracts.task_source import TaskSource
from src.sources.stdin import StdinLineSource
from src.sources.json import JsonlSource
from pathlib import Path
class TestTask:
    def test_task_creation(self):
        task = Task(id="1", payload="test data")
        assert task.id == "1"
        assert task.payload == "test data"
    def test_task_with_different_payload_types(self):
        task1 = Task(id="1", payload="string")
        assert task1.payload == "string"
        task2 = Task(id="52", payload=42)
        assert task2.payload == 42
        task3 = Task(id="3", payload={"GSPD": "1894"})
        assert task3.payload == {"GSPD": "1894"}
        task4 = Task(id="4", payload=[67, 25, 23])
        assert task4.payload == [67, 25, 23]
        task5 = Task(id="5", payload=None)
        assert task5.payload is None
    def test_task_equality(self):
        task1 = Task(id="1", payload="test")
        task2 = Task(id="1", payload="test")
        task3 = Task(id="2", payload="test")
        assert task1 == task2
        assert task1 != task3
class TestTaskSourceContract:
    def test_stdin_source_implements_protocol(self):
        source = StdinLineSource()
        assert isinstance(source, TaskSource)
        assert hasattr(source, 'name')
        assert hasattr(source, 'fetch')
    def test_jsonl_source_implements_protocol(self):
        source = JsonlSource(path=Path("test.jsonl"))
        assert isinstance(source, TaskSource)
        assert hasattr(source, 'name')
        assert hasattr(source, 'fetch')
    def test_source_has_name_attribute(self):
        stdin_source = StdinLineSource()
        jsonl_source = JsonlSource(path=Path("test.jsonl"))
        assert stdin_source.name == "stdin"
        assert jsonl_source.name == "file-jsonl"