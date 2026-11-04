from practice_target import load

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

m = load("p20_testing")


# monkeypatch: environment changes are undone after each test.
def test_base_url_from_env(monkeypatch):
    monkeypatch.setenv("API_BASE_URL", "http://localhost:8000/")
    assert m.get_api_base_url() == "http://localhost:8000"


def test_base_url_default_when_missing_or_empty(monkeypatch):
    monkeypatch.delenv("API_BASE_URL", raising=False)
    assert m.get_api_base_url() == m.DEFAULT_BASE_URL
    monkeypatch.setenv("API_BASE_URL", "")
    assert m.get_api_base_url() == "https://api.example.com"


# patch.object replaces the name where it is looked up: the module's global now.
def test_is_expired_with_patched_clock():
    with patch.object(m, "now", return_value=1000.0) as fake_now:
        assert m.is_expired(900.0, 100.0) is True  # exactly at the boundary
        assert m.is_expired(950.0, 100.0) is False
    assert fake_now.call_count == 2


def test_is_expired_with_monkeypatch(monkeypatch):
    monkeypatch.setattr(m, "now", lambda: 50.0)
    assert m.is_expired(0.0, 60.0) is False


# tmp_path: a fresh pathlib.Path directory for each test.
@pytest.fixture
def config_file(tmp_path):
    path = tmp_path / "app.env"
    path.write_text("A = 1\n\n# comment\nURL=http://x?a=b\n", encoding="utf-8")
    return path


# A module-scoped yield fixture: set up once for this file, torn down after the
# last test that used it. tmp_path is function scoped, so a wider fixture must
# use tmp_path_factory, otherwise pytest raises ScopeMismatch.
@pytest.fixture(scope="module")
def shared_dir(tmp_path_factory):
    path = tmp_path_factory.mktemp("configs")
    yield path
    for file in path.iterdir():
        file.unlink()


def test_read_config(config_file):
    assert m.read_config(config_file) == {"A": "1", "URL": "http://x?a=b"}


def test_read_config_edge_cases(shared_dir):
    empty = shared_dir / "empty.env"
    empty.write_text("", encoding="utf-8")
    assert m.read_config(empty) == {}
    odd = shared_dir / "odd.env"
    odd.write_text("no equals sign here\n  KEY =  \n", encoding="utf-8")
    assert m.read_config(odd) == {"KEY": ""}


# Mock: a stand-in object that records every call made to it.
@pytest.fixture
def fake_client():
    client = Mock(spec=["complete"])  # spec: unknown attributes raise AttributeError
    client.complete.return_value = "  short version \n"
    return client


def test_summarize_calls_client_once(fake_client):
    assert m.summarize("long text", fake_client) == "short version"
    fake_client.complete.assert_called_once_with("Summarize: long text")


@pytest.mark.parametrize("blank", ["", "   ", "\n\t"])
def test_summarize_skips_blank_text(fake_client, blank):
    assert m.summarize(blank, fake_client) == ""
    fake_client.complete.assert_not_called()


# parametrize: one test function, one test case per tuple.
@pytest.mark.parametrize(
    ("text", "expected"),
    [("45s", 45), ("10m", 600), ("1h30m", 5400), ("2h5s", 7205)],
)
def test_parse_duration(text, expected):
    assert m.parse_duration(text) == expected


@pytest.mark.parametrize(
    "bad",
    ["", "90", "1m1h", "abc", "1h 30m"],
    ids=["empty", "no-unit", "wrong-order", "letters", "space"],
)
def test_parse_duration_rejects_bad_input(bad):
    with pytest.raises(ValueError, match="invalid duration"):
        m.parse_duration(bad)


# Async code without any plugin: drive the coroutine with asyncio.run.
def test_retry_succeeds_on_third_call():
    fn = AsyncMock(side_effect=[TimeoutError(), TimeoutError(), "ok"])
    assert asyncio.run(m.call_with_retry(fn)) == "ok"
    assert fn.await_count == 3


def test_retry_gives_up_after_attempts():
    fn = AsyncMock(side_effect=TimeoutError("slow upstream"))
    with pytest.raises(TimeoutError, match="slow upstream"):
        asyncio.run(m.call_with_retry(fn, attempts=2))
    assert fn.await_count == 2


def test_retry_does_not_retry_other_errors():
    fn = AsyncMock(side_effect=ValueError("bad input"))
    with pytest.raises(ValueError):
        asyncio.run(m.call_with_retry(fn))
    assert fn.await_count == 1
