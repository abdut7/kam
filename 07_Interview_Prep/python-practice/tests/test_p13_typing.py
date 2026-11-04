import dataclasses
import math

import pytest

from practice_target import load

m = load("p13_typing")


def test_parse_status():
    assert m.parse_status(" Running ") is m.Status.RUNNING
    assert m.parse_status("DONE") == "done"
    with pytest.raises(ValueError):
        m.parse_status("shiped")


def test_first_or_default():
    assert m.first_or_default([3, 4], 0) == 3
    assert m.first_or_default((x for x in [7, 8]), 0) == 7
    assert m.first_or_default([], "none") == "none"
    assert m.first_or_default(iter(()), None) is None


class Square:
    def __init__(self, side: float) -> None:
        self.side = side

    def area(self) -> float:
        return self.side * self.side


class Circle:
    def __init__(self, r: float) -> None:
        self.r = r

    def area(self) -> float:
        return math.pi * self.r * self.r


def test_total_area():
    assert m.total_area([Square(2), Circle(1)]) == 7.14
    assert m.total_area(s for s in [Square(1), Square(3)]) == 10.0
    assert m.total_area([]) == 0.0


def test_task_dataclass():
    t = m.Task("  write tests ")
    assert dataclasses.is_dataclass(m.Task)
    assert (t.title, t.priority, t.tags) == ("write tests", 3, [])
    a, b = m.Task("a"), m.Task("b")
    a.tags.append("x")
    assert b.tags == [] and a.tags is not b.tags
    assert m.Task("a", 2, ["x"]) == m.Task("a", priority=2, tags=["x"])


def test_task_validation():
    with pytest.raises(ValueError):
        m.Task("   ")
    with pytest.raises(ValueError):
        m.Task("ok", priority=9)
    with pytest.raises(ValueError):
        m.Task("ok", priority=0)


def test_version_parse_and_order():
    assert m.Version.parse(" v1.4.2 ") == m.Version(1, 4, 2)
    assert dataclasses.is_dataclass(m.Version)
    versions = [m.Version.parse(s) for s in ["1.10.0", "1.9.0", "0.9.9"]]
    assert sorted(versions) == [m.Version(0, 9, 9), m.Version(1, 9, 0), m.Version(1, 10, 0)]
    assert max(versions) == m.Version(1, 10, 0)


def test_version_frozen_and_errors():
    v = m.Version(1, 2, 3)
    with pytest.raises(dataclasses.FrozenInstanceError):
        v.major = 2
    assert len({m.Version(1, 2, 3), m.Version(1, 2, 3)}) == 1
    for bad in ["1.4", "1.x.2", "", "1.2.3.4"]:
        with pytest.raises(ValueError):
            m.Version.parse(bad)


def test_validate_payload_ok():
    assert m.validate_payload({"name": " Asha ", "age": 31, "x": 1}) == {"name": "Asha", "age": 31}
    assert m.validate_payload({"name": "Bo", "age": 0}) == {"name": "Bo", "age": 0}


def test_validate_payload_errors():
    with pytest.raises(TypeError):
        m.validate_payload({"name": "Asha", "age": "31"})
    with pytest.raises(TypeError):
        m.validate_payload({"name": "Asha", "age": True})
    with pytest.raises(TypeError):
        m.validate_payload({"age": 3})
    with pytest.raises(ValueError):
        m.validate_payload({"name": "  ", "age": 3})
    with pytest.raises(ValueError):
        m.validate_payload({"name": "Asha", "age": 200})
