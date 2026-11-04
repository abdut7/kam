import json

import pytest

from practice_target import load

m = load("p10_errors")


def test_safe_int():
    assert m.safe_int("42") == 42
    assert m.safe_int(" -7 ") == -7
    assert m.safe_int("4.2", -1) == -1
    assert m.safe_int(None) == 0


def test_get_nested():
    data = {"user": {"tags": ["a", "b"], "profile": None}}
    assert m.get_nested(data, "user", "tags", 1) == "b"
    assert m.get_nested(data, "user", "missing", default="x") == "x"
    assert m.get_nested(data, "user", "tags", 5) is None
    assert m.get_nested(data, "user", "profile", "name", default="?") == "?"


def test_withdraw_and_custom_error():
    assert m.withdraw(100.0, 30.0) == 70.0
    with pytest.raises(m.InsufficientFundsError) as exc:
        m.withdraw(50.0, 80.0)
    assert exc.value.balance == 50.0 and exc.value.amount == 80.0
    assert str(exc.value) == "cannot withdraw 80.0, balance is 50.0"
    with pytest.raises(ValueError):
        m.withdraw(50.0, 0)


def test_insufficient_funds_is_an_exception():
    assert issubclass(m.InsufficientFundsError, Exception)
    err = m.InsufficientFundsError(10.0, 20.0)
    assert err.args == ("cannot withdraw 20.0, balance is 10.0",)


def test_parse_config():
    assert m.parse_config('{"name": "api", "port": 8000}') == {"name": "api", "port": 8000}
    with pytest.raises(m.ConfigError) as exc:
        m.parse_config("{not json")
    assert isinstance(exc.value.__cause__, json.JSONDecodeError)
    assert str(exc.value).startswith("invalid JSON")
    with pytest.raises(m.ConfigError):
        m.parse_config('{"port": 8000}')
    with pytest.raises(m.ConfigError):
        m.parse_config("[1, 2]")


def make_flaky(failures, exc_type=ConnectionError):
    calls = {"n": 0}

    def func():
        calls["n"] += 1
        if calls["n"] <= failures:
            raise exc_type(f"failure {calls['n']}")
        return "ok"

    return func, calls


def test_retry_succeeds_after_failures():
    func, calls = make_flaky(2)
    assert m.retry(func, attempts=3) == "ok"
    assert calls["n"] == 3


def test_retry_gives_up_and_reraises_last():
    func, calls = make_flaky(5)
    with pytest.raises(ConnectionError, match="failure 3"):
        m.retry(func, attempts=3)
    assert calls["n"] == 3


def test_retry_does_not_retry_other_errors():
    func, calls = make_flaky(1, exc_type=KeyError)
    with pytest.raises(KeyError):
        m.retry(func, attempts=3)
    assert calls["n"] == 1
    with pytest.raises(ValueError):
        m.retry(lambda: 1, attempts=0)


def boom(exc):
    def func():
        raise exc
    return func


def test_run_all():
    assert m.run_all([lambda: 1, lambda: 2]) == [1, 2]
    assert m.run_all([]) == []
    with pytest.raises(ExceptionGroup) as exc:
        m.run_all([lambda: 1, boom(ValueError("v")), boom(KeyError("k"))])
    assert str(exc.value) == "2 of 3 calls failed (2 sub-exceptions)"
    assert [type(e) for e in exc.value.exceptions] == [ValueError, KeyError]


def test_run_all_works_with_except_star():
    seen = []
    try:
        m.run_all([boom(ValueError("a")), boom(ValueError("b")), boom(KeyError("k"))])
    except* ValueError as eg:
        seen.append(len(eg.exceptions))
    except* KeyError as eg:
        seen.append(len(eg.exceptions))
    assert seen == [2, 1]
