import json
import os.path

import pytest

from practice_target import load

m = load("p09_modules")


def test_weekday_name():
    assert m.weekday_name("2026-11-02") == "Monday"
    assert m.weekday_name("2024-02-29") == "Thursday"  # leap day
    with pytest.raises(ValueError):
        m.weekday_name("2026-02-30")


def test_filter_by_suffix():
    paths = ["src/app.py", "README.md", "tests/Test_App.PY", "notes.py.txt"]
    assert m.filter_by_suffix(paths, ".py") == ["Test_App.PY", "app.py"]
    assert m.filter_by_suffix(paths, ".md") == ["README.md"]
    assert m.filter_by_suffix([], ".py") == []


def test_run_lengths():
    assert m.run_lengths("aaabcc") == [("a", 3), ("b", 1), ("c", 2)]
    assert m.run_lengths("abca") == [("a", 1), ("b", 1), ("c", 1), ("a", 1)]
    assert m.run_lengths("") == []


def test_parse_json_lines():
    assert m.parse_json_lines('{"a": 1}\n\n{"b": 2}') == [{"a": 1}, {"b": 2}]
    assert m.parse_json_lines("") == []
    with pytest.raises(ValueError, match="line 2"):
        m.parse_json_lines('{"ok": true}\n{bad json}')


def test_extract_ticket_ids():
    assert m.extract_ticket_ids("Fixes API-42 and WEB-7, see API-42") == ["API-42", "WEB-7"]
    assert m.extract_ticket_ids("no tickets here, a-1 and X-9 are too short or lowercase") == []
    assert m.extract_ticket_ids("PAYMENTS-1001: retry") == ["PAYMENTS-1001"]


def test_load_object():
    assert m.load_object("json:dumps") is json.dumps
    assert m.load_object("os.path:join") is os.path.join
    with pytest.raises(ValueError):
        m.load_object("json.dumps")
    with pytest.raises(ImportError):
        m.load_object("no_such_module_xyz:thing")
    with pytest.raises(AttributeError):
        m.load_object("json:no_such_attr")
