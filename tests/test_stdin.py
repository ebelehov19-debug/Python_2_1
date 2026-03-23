import pytest
import sys
from io import StringIO
from unittest.mock import patch
from src.sources.stdin import StdinLineSource, extract_task, create_source
from src.contracts.task import Task
class TestExtractTask:
    def test_extract_valid_two_items(self):
        lines = ["1", "test payload"]
        task_id, payload = extract_task(lines, 1)
        assert task_id == "1"
        assert payload == "test payload"
    
    def test_extract_valid_with_more_items(self):
        lines = ["1", "test", "payload", "with", "colons"]
        task_id, payload = extract_task(lines, 1)
        
        assert task_id == "1"
        assert payload == "test" 
    
    def test_extract_with_less_than_two_items(self):
        lines = ["only_one"]
        with pytest.raises(ValueError, match="Task must contain at least 2 items"):
            extract_task(lines, 5)
    
    def test_extract_with_empty_list(self):
        lines = []
        with pytest.raises(ValueError, match="Task must contain at least 2 items"):
            extract_task(lines, 10)
    
    def test_extract_error_message_contains_line_number(self):
        lines = ["incomplete"]
        
        with pytest.raises(ValueError) as exc_info:
            extract_task(lines, 42)
        assert "42" in str(exc_info.value)
        assert "at least 2 items" in str(exc_info.value)


class TestStdinLineSource:
    def test_source_has_correct_name(self):
        source = StdinLineSource()
        assert source.name == "stdin"
    
    def test_source_implements_fetch_method(self):
        source = StdinLineSource()
        assert hasattr(source, 'fetch')
        assert callable(source.fetch)
    
    def test_fetch_from_single_line(self):
        fake_stream = StringIO("1:first task\n")
        source = StdinLineSource(stream=fake_stream)
        tasks = list(source.fetch())
        assert len(tasks) == 1
        assert tasks[0].id == "1"
        assert tasks[0].payload == "first task\n"
    
    def test_fetch_from_multiple_lines(self):
        fake_stream = StringIO(
            "1:first task\n"
            "2:second task\n"
            "3:third task\n"
        )
        source = StdinLineSource(stream=fake_stream)
        tasks = list(source.fetch())
        assert len(tasks) == 3
        assert tasks[0].id == "1"
        assert tasks[0].payload == "first task\n"
        assert tasks[1].id == "2"
        assert tasks[1].payload == "second task\n"
        assert tasks[2].id == "3"
        assert tasks[2].payload == "third task\n"
    def test_fetch_skip_empty_lines(self):
        fake_stream = StringIO(
            "1:first task\n"
            "\n"
            "2:second task\n"
            "\n"
            "\n"
            "3:third task\n"
        )
        source = StdinLineSource(stream=fake_stream)
        tasks = list(source.fetch())
        assert len(tasks) == 3
        assert tasks[0].id == "1"
        assert tasks[1].id == "2"
        assert tasks[2].id == "3"
    
    def test_fetch_skip_lines_with_only_whitespace(self):
        """Тест пропуска строк, содержащих только пробелы."""
        fake_stream = StringIO(
            "1:first task\n"
            "   \n"
            "2:second task\n"
            "\t\n"
            "3:third task\n"
        )
        source = StdinLineSource(stream=fake_stream)
        tasks = list(source.fetch())
        assert len(tasks) == 3
    def test_fetch_with_colons_in_payload(self):
        """Тест обработки payload, содержащего двоеточия."""
        fake_stream = StringIO("1:payload:with:multiple:colons\n")
        source = StdinLineSource(stream=fake_stream)
        tasks = list(source.fetch())
        assert len(tasks) == 1
        assert tasks[0].id == "1"
        assert tasks[0].payload == "payload"
    def test_fetch_with_whitespace_in_line(self):
        """Тест обработки строк с пробелами."""
        fake_stream = StringIO(" 1:first task")
        source = StdinLineSource(stream=fake_stream)
        tasks = list(source.fetch())
        assert len(tasks) == 1
        assert tasks[0].id == " 1"
        assert tasks[0].payload == "first task"
    def test_fetch_with_numeric_payload(self):
        """Тест обработки числового payload (как строки)."""
        fake_stream = StringIO("1:42")
        source = StdinLineSource(stream=fake_stream)
        tasks = list(source.fetch())
        assert len(tasks) == 1
        assert tasks[0].id == "1"
        assert tasks[0].payload == "42"
    def test_fetch_empty_stream(self):
        """Тест чтения из пустого потока."""
        fake_stream = StringIO("")
        source = StdinLineSource(stream=fake_stream)
        tasks = list(source.fetch())
        assert len(tasks) == 0
    def test_iteration_protocol(self):
        fake_stream = StringIO(
            "1:first task\n"
            "2:second task\n"
        )
        source = StdinLineSource(stream=fake_stream).fetch()
        tasks = []
        for task in source:
            tasks.append(task)
        assert len(tasks) == 2
        assert tasks[0].id == "1"
        assert tasks[1].id == "2"
    def test_multiple_iterations(self):
        fake_stream = StringIO(
            "1:first task\n"
            "2:second task\n"
        )
        source = StdinLineSource(stream=fake_stream)
        tasks1 = list(source.fetch())
        tasks2 = list(source.fetch())
        assert len(tasks1) == 2
        assert len(tasks2) == 0
class TestCreateSource:
    def test_create_source_returns_instance(self):
        source = create_source()
        assert isinstance(source, StdinLineSource)
    def test_create_source_uses_default_stdin(self):
        source = create_source()
        assert source.stream == sys.stdin


class TestIntegration:
    def test_contract_compliance(self):
        from src.contracts.task_source import TaskSource
        source = StdinLineSource()
        assert isinstance(source, TaskSource)
        assert hasattr(source, 'name')
        assert source.name == "stdin"
        assert hasattr(source, 'fetch')
        assert callable(source.fetch)
    def test_large_input(self):
        """Тест обработки большого количества строк."""
        lines = [f"{i}:task {i}\n" for i in range(1000)]
        fake_stream = StringIO("".join(lines))
        source = StdinLineSource(stream=fake_stream)
        tasks = list(source.fetch())
        assert len(tasks) == 1000
        assert tasks[0].id == "0"
        assert tasks[499].id == "499"
        assert tasks[999].id == "999"