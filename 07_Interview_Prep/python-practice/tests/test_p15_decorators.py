import os
import time

import pytest

from practice_target import load

m = load("p15_decorators")


class Boom(Exception):
    """A test-only error (NotImplementedError subclasses RuntimeError, so avoid that)."""


def test_shout():
    @m.shout
    def greet(name: str) -> str:
        """Say hi."""
        return f"hi {name}"

    assert greet("asha") == "HI ASHA"
    assert greet(name="ravi") == "HI RAVI"
    assert greet.__name__ == "greet" and greet.__doc__ == "Say hi."


def test_count_calls():
    @m.count_calls
    def add(a: int, b: int = 0) -> int:
        return a + b

    assert add.calls == 0
    assert add(1, 2) == 3 and add(5, b=1) == 6
    assert add.calls == 2
    assert add.__name__ == "add"


def test_count_calls_counts_failures():
    @m.count_calls
    def boom() -> None:
        raise Boom("x")

    with pytest.raises(Boom):
        boom()
    assert boom.calls == 1


def test_timer():
    t = m.Timer()
    assert t.elapsed is None
    with t as same:
        time.sleep(0.01)
    assert same is t
    assert isinstance(t.elapsed, float) and t.elapsed >= 0.01


def test_timer_does_not_swallow():
    with pytest.raises(ValueError):
        with m.Timer() as t:
            raise ValueError("boom")
    assert t.elapsed is not None


def flaky(failures: int, exc: type[BaseException]):
    state = {"calls": 0}

    def call() -> str:
        state["calls"] += 1
        if state["calls"] <= failures:
            raise exc("fail")
        return "ok"

    return call, state


def test_retry_succeeds_after_failures():
    call, state = flaky(2, ConnectionError)
    wrapped = m.retry(times=3, exceptions=(ConnectionError,))(call)
    assert wrapped() == "ok" and state["calls"] == 3
    assert wrapped.__name__ == "call"


def test_retry_gives_up_and_filters():
    call, state = flaky(5, ConnectionError)
    with pytest.raises(ConnectionError):
        m.retry(times=3, exceptions=(ConnectionError,))(call)()
    assert state["calls"] == 3
    call2, state2 = flaky(5, KeyError)
    with pytest.raises(KeyError):
        m.retry(times=3, exceptions=(ConnectionError,))(call2)()
    assert state2["calls"] == 1  # not retried
    with pytest.raises(ValueError):
        m.retry(times=0)


def test_router():
    router = m.Router()

    @router.get("/health")
    def health() -> dict:
        return {"ok": True}

    @router.post("/items")
    def create(name: str) -> dict:
        return {"created": name}

    assert router.dispatch("GET", "/health") == {"ok": True}
    assert router.dispatch("POST", "/items", name="pen") == {"created": "pen"}
    assert health() == {"ok": True}  # returned unchanged
    assert router.routes[("GET", "/health")] is health
    with pytest.raises(LookupError):
        router.dispatch("GET", "/missing")


def test_temp_env_sets_and_restores():
    os.environ.pop("P15_NEW", None)
    os.environ["P15_OLD"] = "before"
    try:
        with m.temp_env(P15_NEW="1", P15_OLD="during"):
            assert os.environ["P15_NEW"] == "1"
            assert os.environ["P15_OLD"] == "during"
        assert "P15_NEW" not in os.environ
        assert os.environ["P15_OLD"] == "before"
    finally:
        os.environ.pop("P15_OLD", None)


def test_temp_env_restores_on_error():
    os.environ.pop("P15_TMP", None)
    with pytest.raises(Boom):
        with m.temp_env(P15_TMP="x"):
            raise Boom("test failed")
    assert "P15_TMP" not in os.environ
