import pytest
from src.sources.repository import REGISTRY, register_source
from src.contracts.task_source import TaskSource


class TestRegistry:
    def test_registry_is_dict(self):
        assert isinstance(REGISTRY, dict)

    def test_registry_contains_builtin_sources(self):
        assert "stdin" in REGISTRY
        assert "file-jsonl" in REGISTRY

    def test_register_function_source(self):
        @register_source("test-function")
        def test_source():
            return object()
        assert "test-function" in REGISTRY
        assert REGISTRY["test-function"] == test_source

    def test_register_class_source(self):
        class TestClass:
            name = "test"
            def fetch(self):
                yield from []
        @register_source("test-class")
        def create_test():
            return TestClass()
        assert "test-class" in REGISTRY
        assert REGISTRY["test-class"] == create_test

    def test_register_multiple_sources(self):
        @register_source("source-a")
        def source_a():
            pass
        @register_source("source-b")
        def source_b():
            pass
        assert "source-a" in REGISTRY
        assert "source-b" in REGISTRY

    def test_register_overwrites_existing(self):
        @register_source("same-name")
        def first():
            return "first"
        @register_source("same-name")
        def second():
            return "second"
        assert REGISTRY["same-name"] == second

    def test_register_preserves_function(self):
        @register_source("preserve")
        def original():
            return "value"
        assert original() == "value"

    def test_register_with_class_decorator(self):
        @register_source("decorated-class")
        class DecoratedClass:
            name = "decorated"
            def fetch(self):
                yield from []
        assert "decorated-class" in REGISTRY
        assert REGISTRY["decorated-class"] == DecoratedClass

    def test_registry_keys_are_strings(self):
        for key in REGISTRY.keys():
            assert isinstance(key, str)

    def test_registry_values_are_callable(self):
        for value in REGISTRY.values():
            assert callable(value)


class TestSourceFactory:
    def test_stdin_factory_returns_callable(self):
        assert callable(REGISTRY["stdin"])

    def test_jsonl_factory_returns_callable(self):
        assert callable(REGISTRY["file-jsonl"])

    def test_stdin_factory_creates_source(self):
        from src.sources.stdin import StdinLineSource
        source = REGISTRY["stdin"]()
        assert isinstance(source, StdinLineSource)

    def test_jsonl_factory_creates_source(self, tmp_path):
        from src.sources.json import JsonlSource
        jsonl_file = tmp_path / "test.jsonl"
        source = REGISTRY["file-jsonl"](jsonl_file)
        assert isinstance(source, JsonlSource)
        assert source.path == jsonl_file