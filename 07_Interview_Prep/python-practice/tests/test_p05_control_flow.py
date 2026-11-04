import pytest

from practice_target import load

m = load("p05_control_flow")


def test_classify_status():
    assert m.classify_status(200) == "success"
    assert m.classify_status(301) == "redirect"
    assert m.classify_status(404) == "client_error"
    assert m.classify_status(503) == "server_error"
    assert m.classify_status(101) == "informational"
    assert m.classify_status(600) == "unknown"


def test_find_first_over():
    assert m.find_first_over([3, 9, 12, 15], 10) == 2
    assert m.find_first_over([11], 10) == 0
    assert m.find_first_over([1, 2, 10], 10) is None
    assert m.find_first_over([], 0) is None


def test_pair_up():
    assert m.pair_up(["asha", "ravi"], [91, 78]) == ["asha: 91", "ravi: 78"]
    assert m.pair_up([], []) == []
    with pytest.raises(ValueError):
        m.pair_up(["asha", "ravi", "meera"], [91, 78])


def flaky(failures: int, value: str = "ok"):
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        if calls["n"] <= failures:
            raise ConnectionError(f"attempt {calls['n']} failed")
        return value

    return fn, calls


def test_call_with_retries():
    fn, calls = flaky(2)
    assert m.call_with_retries(fn, 3) == "ok"
    assert calls["n"] == 3

    fn, calls = flaky(5)
    with pytest.raises(ConnectionError, match="attempt 2"):
        m.call_with_retries(fn, 2)
    assert calls["n"] == 2

    def broken():
        calls["n"] += 1
        raise KeyError("bug")

    calls["n"] = 0
    with pytest.raises(KeyError):
        m.call_with_retries(broken, 5)
    assert calls["n"] == 1

    with pytest.raises(ValueError):
        m.call_with_retries(lambda: "ok", 0)


def test_parse_command():
    assert m.parse_command("") == ("noop",)
    assert m.parse_command("GO North") == ("move", "north")
    assert m.parse_command("pick up lamp") == ("take", "lamp")
    assert m.parse_command("drop key coin") == ("drop", ["key", "coin"])
    assert m.parse_command("exit") == ("quit",)
    assert m.parse_command("drop") == ("error", "drop")
    assert m.parse_command("go") == ("error", "go")


def test_route_event():
    assert m.route_event({"type": "message", "text": "  hi there "}) == "reply:hi there"
    assert m.route_event({"type": "message", "text": "   "}) == "ignore"
    assert m.route_event({"type": "tool_call", "name": "search", "args": {"q": "x"}, "id": 7}) == "run:search"
    assert m.route_event({"type": "tool_call", "name": "search", "args": ["x"]}) == "ignore"
    assert m.route_event({"type": "payment", "amount": 25_000}) == "review"
    assert m.route_event({"type": "payment", "amount": 99.5}) == "approve"
    assert m.route_event({"type": "payment", "amount": "500"}) == "ignore"
    assert m.route_event({}) == "ignore"
