import pytest
from io import StringIO
from src.inbox.core import TaskProcessor
from src.contracts.task import Task
from src.contracts.task_source import TaskSource
from src.sources.stdin import StdinLineSource
from src.sources.json import JsonlSource


class MockTaskSource:
    name = "mock"
    def __init__(self, tasks=None):
        self.tasks = tasks or []
    def fetch(self):
        return iter(self.tasks)
    def __iter__(self):
        return iter(self.fetch())


class TestTaskProcessor:
    def test_init_with_no_sources(self):
        processor = TaskProcessor()
        assert processor._sources == []

    def test_init_with_none(self):
        processor = TaskProcessor(None)
        assert processor._sources == []

    def test_init_with_single_source(self):
        source = MockTaskSource()
        processor = TaskProcessor([source])
        assert len(processor._sources) == 1
        assert processor._sources[0] == source

    def test_init_with_multiple_sources(self):
        source1 = MockTaskSource()
        source2 = MockTaskSource()
        processor = TaskProcessor([source1, source2])
        assert len(processor._sources) == 2

    def test_iter_task_with_no_sources(self):
        processor = TaskProcessor()
        tasks = list(processor.iter_task())
        assert tasks == []

    def test_iter_task_with_single_source(self):
        tasks = [Task(id="1", payload="task1"), Task(id="2", payload="task2")]
        source = MockTaskSource(tasks)
        processor = TaskProcessor([source])
        result = list(processor.iter_task())
        assert len(result) == 2
        assert result[0].id == "1"
        assert result[1].id == "2"

    def test_iter_task_with_multiple_sources(self):
        source1 = MockTaskSource([Task(id="1", payload="from source1")])
        source2 = MockTaskSource([Task(id="2", payload="from source2")])
        processor = TaskProcessor([source1, source2])
        result = list(processor.iter_task())
        assert len(result) == 2
        assert result[0].payload == "from source1"
        assert result[1].payload == "from source2"

    def test_iter_task_with_stdin_source(self):
        fake_stream = StringIO("1:task1\n2:task2\n")
        source = StdinLineSource(stream=fake_stream)
        processor = TaskProcessor([source])
        result = list(processor.iter_task())
        assert len(result) == 2
        assert result[0].id == "1"
        assert result[1].id == "2"

    def test_iter_task_with_jsonl_source(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"id": "1", "payload": "task1"}\n{"id": "2", "payload": "task2"}\n')
        source = JsonlSource(path=jsonl_file)
        processor = TaskProcessor([source])
        result = list(processor.iter_task())
        assert len(result) == 2
        assert result[0].id == "1"
        assert result[1].id == "2"

    def test_iter_task_with_mixed_sources(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"id": "1", "payload": "from jsonl"}\n')
        jsonl_source = JsonlSource(path=jsonl_file)
        fake_stream = StringIO("2:from stdin\n")
        stdin_source = StdinLineSource(stream=fake_stream)
        processor = TaskProcessor([jsonl_source, stdin_source])
        result = list(processor.iter_task())
        assert len(result) == 2
        ids = [task.id for task in result]
        assert "1" in ids
        assert "2" in ids

    def test_iter_task_with_invalid_source(self):
        class InvalidSource:
            pass
        processor = TaskProcessor([InvalidSource()])
        with pytest.raises(TypeError, match="Source object must be TaskSource"):
            list(processor.iter_task())

    def test_iter_task_with_source_missing_name(self):
        class MissingNameSource:
            def fetch(self):
                yield from []
        processor = TaskProcessor([MissingNameSource()])
        with pytest.raises(TypeError, match="Source object must be TaskSource"):
            list(processor.iter_task())

    def test_iter_task_preserves_order(self):
        tasks = [Task(id=f"{i}", payload=f"task{i}") for i in range(5)]
        source = MockTaskSource(tasks)
        processor = TaskProcessor([source])
        result = list(processor.iter_task())
        for i in range(5):
            assert result[i].id == str(i)

    def test_iter_task_lazy_evaluation(self):
        source = MockTaskSource([Task(id="1", payload="delayed")])
        processor = TaskProcessor([source])
        iterator = processor.iter_task()
        assert hasattr(iterator, '__iter__')
        assert hasattr(iterator, '__next__')

    def test_multiple_iterations(self):
        tasks = [Task(id="1", payload="task1")]
        source = MockTaskSource(tasks)
        processor = TaskProcessor([source])
        result1 = list(processor.iter_task())
        result2 = list(processor.iter_task())
        assert len(result1) == 1
        assert len(result2) == 1
        assert result1[0].id == result2[0].id

    def test_iter_task_with_empty_source(self):
        source = MockTaskSource([])
        processor = TaskProcessor([source])
        result = list(processor.iter_task())
        assert result == []

    def test_iter_task_type_check(self):
        source = MockTaskSource()
        processor = TaskProcessor([source])
        result = list(processor.iter_task())
        for task in result:
            assert isinstance(task, Task)

    def test_processor_accepts_task_source_subclass(self):
        class CustomSource(TaskSource):
            name = "custom"
            def fetch(self):
                yield Task(id="1", payload="test")
        processor = TaskProcessor([CustomSource()])
        result = list(processor.iter_task())
        assert len(result) == 1
        assert result[0].id == "1"


class TestTaskProcessorIntegration:
    def test_full_workflow_stdin_only(self):
        fake_stream = StringIO("1:task1\n2:task2\n3:task3\n")
        source = StdinLineSource(stream=fake_stream)
        processor = TaskProcessor([source])
        tasks = list(processor.iter_task())
        assert len(tasks) == 3
        assert tasks[0].id == "1"
        assert tasks[1].id == "2"
        assert tasks[2].id == "3"

    def test_full_workflow_jsonl_only(self, tmp_path):
        jsonl_file = tmp_path / "tasks.jsonl"
        jsonl_file.write_text(
            '{"id": "1", "payload": "first"}\n'
            '{"id": "2", "payload": "second"}\n'
        )
        source = JsonlSource(path=jsonl_file)
        processor = TaskProcessor([source])
        tasks = list(processor.iter_task())
        assert len(tasks) == 2
        assert tasks[0].payload == "first"
        assert tasks[1].payload == "second"

