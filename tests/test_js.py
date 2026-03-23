import pytest
from pathlib import Path
from src.sources.json import JsonlSource, parse_json_file, create_json_source
from src.contracts.task_source import TaskSource


class TestParseJsonFile:
    def test_parse_valid_json(self):
        data = parse_json_file('{"id": "1", "payload": "test"}', "test.jsonl", 1)
        assert data["id"] == "1"
        assert data["payload"] == "test"

    def test_parse_json_without_payload(self):
        data = parse_json_file('{"id": "1"}', "test.jsonl", 1)
        assert data["id"] == "1"
        assert "payload" not in data

    def test_parse_json_with_numeric_id(self):
        data = parse_json_file('{"id": 123, "payload": "test"}', "test.jsonl", 1)
        assert data["id"] == 123

    def test_parse_json_with_complex_payload(self):
        json_str = '{"id": "1", "payload": {"key": "value", "list": [1, 2, 3]}}'
        data = parse_json_file(json_str, "test.jsonl", 1)
        assert data["payload"]["key"] == "value"
        assert data["payload"]["list"] == [1, 2, 3]

    def test_parse_json_with_array_payload(self):
        json_str = '{"id": "1", "payload": [1, 2, 3, 4]}'
        data = parse_json_file(json_str, "test.jsonl", 1)
        assert data["payload"] == [1, 2, 3, 4]

    def test_parse_json_with_null_payload(self):
        json_str = '{"id": "1", "payload": null}'
        data = parse_json_file(json_str, "test.jsonl", 1)
        assert data["payload"] is None

    def test_parse_invalid_json(self):
        with pytest.raises(ValueError, match="Bad JSON at test.jsonl:5:"):
            parse_json_file('{invalid json}', "test.jsonl", 5)

    def test_parse_json_with_trailing_comma(self):
        with pytest.raises(ValueError, match="Bad JSON"):
            parse_json_file('{"id": "1",}', "test.jsonl", 1)

    def test_parse_json_with_unicode(self):
        json_str = '{"id": "1", "payload": "Привет мир 🎉"}'
        data = parse_json_file(json_str, "test.jsonl", 1)
        assert data["payload"] == "Привет мир 🎉"

    def test_parse_json_escaped_chars(self):
        json_str = '{"id": "1", "payload": "line1\\nline2\\ttab"}'
        data = parse_json_file(json_str, "test.jsonl", 1)
        assert "line1\nline2\ttab" in data["payload"]


class TestJsonlSource:
    def test_source_has_correct_name(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        source = JsonlSource(path=jsonl_file)
        assert source.name == "file-jsonl"

    def test_source_implements_fetch_method(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        source = JsonlSource(path=jsonl_file)
        assert hasattr(source, 'fetch')
        assert callable(source.fetch)

    def test_fetch_from_single_line(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"id": "1", "payload": "first task"}\n')
        source = JsonlSource(path=jsonl_file)
        tasks = list(source.fetch())
        assert len(tasks) == 1
        assert tasks[0].id == "1"
        assert tasks[0].payload == "first task"

    def test_fetch_from_multiple_lines(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text(
            '{"id": "1", "payload": "first"}\n'
            '{"id": "2", "payload": "second"}\n'
            '{"id": "3", "payload": "third"}\n'
        )
        source = JsonlSource(path=jsonl_file)
        tasks = list(source.fetch())
        assert len(tasks) == 3
        assert tasks[0].id == "1"
        assert tasks[0].payload == "first"
        assert tasks[1].id == "2"
        assert tasks[1].payload == "second"
        assert tasks[2].id == "3"
        assert tasks[2].payload == "third"

    def test_fetch_with_different_payload_types(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text(
            '{"id": "1", "payload": "string"}\n'
            '{"id": "2", "payload": 42}\n'
            '{"id": "3", "payload": 3.14}\n'
            '{"id": "4", "payload": true}\n'
            '{"id": "5", "payload": false}\n'
            '{"id": "6", "payload": null}\n'
            '{"id": "7", "payload": {"key": "value"}}\n'
            '{"id": "8", "payload": [1, 2, 3]}\n'
        )
        source = JsonlSource(path=jsonl_file)
        tasks = list(source.fetch())
        assert len(tasks) == 8
        assert tasks[0].payload == "string"
        assert tasks[1].payload == 42
        assert tasks[2].payload == 3.14
        assert tasks[3].payload is True
        assert tasks[4].payload is False
        assert tasks[5].payload is None
        assert tasks[6].payload == {"key": "value"}
        assert tasks[7].payload == [1, 2, 3]

    def test_fetch_skip_empty_lines(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text(
            '{"id": "1", "payload": "first"}\n'
            '\n'
            '{"id": "2", "payload": "second"}\n'
            '\n'
            '\n'
            '{"id": "3", "payload": "third"}\n'
        )
        source = JsonlSource(path=jsonl_file)
        tasks = list(source.fetch())
        assert len(tasks) == 3

    def test_fetch_skip_lines_with_only_whitespace(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text(
            '{"id": "1", "payload": "first"}\n'
            '   \n'
            '{"id": "2", "payload": "second"}\n'
            '\t\n'
            '{"id": "3", "payload": "third"}\n'
        )
        source = JsonlSource(path=jsonl_file)
        tasks = list(source.fetch())
        assert len(tasks) == 3

    def test_fetch_empty_file(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text("")
        source = JsonlSource(path=jsonl_file)
        tasks = list(source.fetch())
        assert len(tasks) == 0

    def test_fetch_file_with_only_empty_lines(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text("\n\n\n  \n\t\n\n")
        source = JsonlSource(path=jsonl_file)
        tasks = list(source.fetch())
        assert len(tasks) == 0

    def test_iteration_protocol(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text(
            '{"id": "1", "payload": "first"}\n'
            '{"id": "2", "payload": "second"}\n'
        )
        source = JsonlSource(path=jsonl_file)
        tasks = []
        for task in source.fetch():
            tasks.append(task)
        assert len(tasks) == 2
        assert tasks[0].id == "1"
        assert tasks[1].id == "2"

    def test_multiple_iterations(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text(
            '{"id": "1", "payload": "first"}\n'
            '{"id": "2", "payload": "second"}\n'
        )
        source = JsonlSource(path=jsonl_file)
        tasks1 = list(source.fetch())
        tasks2 = list(source.fetch())
        assert len(tasks1) == 2
        assert len(tasks2) == 2
        assert tasks1[0].id == tasks2[0].id

    def test_file_not_found(self, tmp_path):
        non_existent = tmp_path / "does_not_exist.jsonl"
        source = JsonlSource(path=non_existent)
        with pytest.raises(FileNotFoundError):
            list(source.fetch())

    def test_large_file(self, tmp_path):
        jsonl_file = tmp_path / "large.jsonl"
        lines = [f'{{"id": "{i}", "payload": "task {i}"}}\n' for i in range(1000)]
        jsonl_file.write_text("".join(lines))
        source = JsonlSource(path=jsonl_file)
        tasks = list(source.fetch())
        assert len(tasks) == 1000
        assert tasks[0].id == "0"
        assert tasks[499].id == "499"
        assert tasks[999].id == "999"


class TestCreateSource:
    def test_create_source_returns_instance(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        source = create_json_source(jsonl_file)
        assert isinstance(source, JsonlSource)

    def test_create_source_preserves_path(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        source = create_json_source(jsonl_file)
        assert source.path == jsonl_file


class TestIntegration:
    def test_contract_compliance(self, tmp_path):
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"id": "1", "payload": "test"}\n')
        source = JsonlSource(path=jsonl_file)
        assert isinstance(source, TaskSource)
        assert hasattr(source, 'name')
        assert source.name == "file-jsonl"
        assert hasattr(source, 'fetch')
        assert callable(source.fetch)

    def test_full_workflow(self, tmp_path):
        jsonl_file = tmp_path / "tasks.jsonl"
        jsonl_file.write_text(
            '{"id": "1", "payload": "first"}\n'
            '{"id": "2", "payload": "second"}\n'
            '{"id": "3", "payload": "third"}\n'
        )
        source = JsonlSource(path=jsonl_file)
        tasks = list(source.fetch())
        assert len(tasks) == 3
        assert tasks[0].id == "1"
        assert tasks[1].id == "2"
        assert tasks[2].id == "3"

    def test_special_characters_in_payload(self, tmp_path):
        jsonl_file = tmp_path / "special.jsonl"
        jsonl_file.write_text(
            '{"id": "1", "payload": "line with \\"quotes\\""}\n'
            "{\"id\": \"2\", \"payload\": \"line with 'single quotes'\"}\n"
            '{"id": "3", "payload": "line with\\ttab"}\n'
            '{"id": "4", "payload": "line with\\nnewline"}\n'
        )
        source = JsonlSource(path=jsonl_file)
        tasks = list(source.fetch())
        assert len(tasks) == 4
        assert '"quotes"' in tasks[0].payload
        assert "'single quotes'" in tasks[1].payload
        assert "tab" in tasks[2].payload
        assert "newline" in tasks[3].payload