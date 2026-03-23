import pytest
from src.contracts.task_source import TaskSource
from src.sources.stdin import StdinLineSource
from src.sources.json import JsonlSource
from collections.abc import Iterable

class TestTaskSourceProtocol:
    def test_stdin_source_implements_protocol(self):
        source = StdinLineSource()
        assert isinstance(source, TaskSource)

    def test_jsonl_source_implements_protocol(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        source = JsonlSource(path=jsonl_file)
        assert isinstance(source, TaskSource)

    def test_stdin_source_has_name_attribute(self):
        source = StdinLineSource()
        assert hasattr(source, 'name')
        assert isinstance(source.name, str)
        assert source.name == "stdin"

    def test_jsonl_source_has_name_attribute(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        source = JsonlSource(path=jsonl_file)
        assert hasattr(source, 'name')
        assert isinstance(source.name, str)
        assert source.name == "file-jsonl"

    def test_stdin_source_has_fetch_method(self):
        source = StdinLineSource()
        assert hasattr(source, 'fetch')
        assert callable(source.fetch)

    def test_jsonl_source_has_fetch_method(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        source = JsonlSource(path=jsonl_file)
        assert hasattr(source, 'fetch')
        assert callable(source.fetch)

    def test_stdin_source_fetch_returns_iterable(self):
        source = StdinLineSource()
        result = source.fetch()
        assert isinstance(result, Iterable)

    def test_jsonl_source_fetch_returns_iterable(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"id": "1", "payload": "test"}\n')
        source = JsonlSource(path=jsonl_file)
        result = source.fetch()
        assert isinstance(result, Iterable)

    def test_custom_class_implements_protocol(self):
        class CustomSource:
            name = "custom"
            def fetch(self):
                yield from []
        source = CustomSource()
        assert isinstance(source, TaskSource)

    def test_class_without_name_not_implements(self):
        class NoNameSource:
            def fetch(self):
                yield from []
        source = NoNameSource()
        assert not isinstance(source, TaskSource)

    def test_class_without_fetch_not_implements(self):
        class NoFetchSource:
            name = "test"
        source = NoFetchSource()
        assert not isinstance(source, TaskSource)