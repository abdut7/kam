import json
from datetime import date, datetime

import pytest

from practice_target import load

m = load("p11_files_json")


def test_count_matching_lines(tmp_path):
    log = tmp_path / "app.log"
    log.write_text("ERROR a\nINFO b\nERROR c\nwarn ERROR inside\n", encoding="utf-8")
    assert m.count_matching_lines(log, "ERROR") == 3
    assert m.count_matching_lines(log, "DEBUG") == 0
    empty = tmp_path / "empty.log"
    empty.write_text("", encoding="utf-8")
    assert m.count_matching_lines(empty, "ERROR") == 0


def test_find_files(tmp_path):
    (tmp_path / "sub" / "deep").mkdir(parents=True)
    (tmp_path / "a.json").write_text("{}")
    (tmp_path / "sub" / "b.json").write_text("{}")
    (tmp_path / "sub" / "deep" / "c.json").write_text("{}")
    (tmp_path / "notes.txt").write_text("x")
    assert m.find_files(tmp_path, ".json") == ["a.json", "sub/b.json", "sub/deep/c.json"]
    assert m.find_files(tmp_path, ".csv") == []


def test_to_json_handles_dates_and_sets():
    text = m.to_json({"b": {3, 1, 2}, "a": datetime(2026, 11, 2, 10, 30), "d": date(2026, 1, 5)})
    assert json.loads(text) == {"a": "2026-11-02T10:30:00", "b": [1, 2, 3], "d": "2026-01-05"}
    assert text.index('"a"') < text.index('"b"')  # sort_keys
    assert m.to_json({"name": "Zoë"}) == '{\n  "name": "Zoë"\n}'


def test_to_json_rejects_unknown_types():
    with pytest.raises(TypeError):
        m.to_json({"x": object()})


def test_env_bool(monkeypatch):
    monkeypatch.delenv("FEATURE_X", raising=False)
    assert m.env_bool("FEATURE_X") is False
    assert m.env_bool("FEATURE_X", default=True) is True
    monkeypatch.setenv("FEATURE_X", " False ")
    assert m.env_bool("FEATURE_X", default=True) is False
    monkeypatch.setenv("FEATURE_X", "YES")
    assert m.env_bool("FEATURE_X") is True


def test_env_bool_rejects_garbage(monkeypatch):
    monkeypatch.setenv("FEATURE_X", "maybe")
    with pytest.raises(ValueError, match="FEATURE_X"):
        m.env_bool("FEATURE_X")


def test_clean_users_csv(tmp_path):
    src = tmp_path / "users.csv"
    src.write_text(
        "name,email,age\n"
        " Asha ,ASHA@X.COM, 31\n"
        "Ravi,,40\n"
        '"Khan, Imran",imran@x.com,\n',
        encoding="utf-8",
    )
    dst = tmp_path / "out" / "clean.csv"
    dst.parent.mkdir()
    assert m.clean_users_csv(src, dst) == 2
    lines = dst.read_text(encoding="utf-8").splitlines()
    assert lines == ["name,email,age", "Asha,asha@x.com,31", '"Khan, Imran",imran@x.com,']


def test_clean_users_csv_header_only(tmp_path):
    src = tmp_path / "users.csv"
    src.write_text("name,email,age\n", encoding="utf-8")
    dst = tmp_path / "clean.csv"
    assert m.clean_users_csv(src, dst) == 0
    assert dst.read_text(encoding="utf-8").splitlines() == ["name,email,age"]


def test_atomic_write_json(tmp_path):
    target = tmp_path / "state" / "run.json"
    m.atomic_write_json(target, {"step": 3})
    assert json.loads(target.read_text(encoding="utf-8")) == {"step": 3}
    m.atomic_write_json(target, {"step": 4})
    assert json.loads(target.read_text(encoding="utf-8")) == {"step": 4}
    assert [p.name for p in target.parent.iterdir()] == ["run.json"]


def test_atomic_write_json_failure_keeps_old_file(tmp_path):
    target = tmp_path / "run.json"
    m.atomic_write_json(target, {"ok": True})
    with pytest.raises(TypeError):
        m.atomic_write_json(target, {"bad": object()})
    assert json.loads(target.read_text(encoding="utf-8")) == {"ok": True}
    assert [p.name for p in tmp_path.iterdir()] == ["run.json"]
