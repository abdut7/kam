from practice_target import load
from decimal import Decimal

import pytest

m = load("p03_variables")


def test_page_limit():
    assert m.page_limit(None) == 20
    assert m.page_limit(0) == 0
    assert m.page_limit(500) == 100
    assert m.page_limit(-5) == 0
    assert m.page_limit(None, default=50, maximum=40) == 50


def test_validate_quantity():
    assert m.validate_quantity(3) == 3
    assert m.validate_quantity(99) == 99
    with pytest.raises(TypeError):
        m.validate_quantity(True)
    with pytest.raises(TypeError):
        m.validate_quantity("3")
    with pytest.raises(ValueError):
        m.validate_quantity(0)


def test_clone_with_tag():
    doc = {"id": 1, "tags": ["a"], "meta": {"owner": "ada"}}
    result = m.clone_with_tag(doc, "b")
    assert result == {"id": 1, "tags": ["a", "b"], "meta": {"owner": "ada"}}
    assert doc["tags"] == ["a"]
    assert result["meta"] is not doc["meta"]
    assert m.clone_with_tag({"id": 2}, "new") == {"id": 2, "tags": ["new"]}


def test_to_number():
    value = m.to_number(" 42 ")
    assert value == 42 and type(value) is int
    assert m.to_number("-7") == -7
    big = m.to_number("1e3")
    assert big == 1000.0 and type(big) is float
    assert m.to_number("2.50") == 2.5
    for bad in ["abc", "", "nan", "inf"]:
        with pytest.raises(ValueError):
            m.to_number(bad)


def test_sum_money():
    assert m.sum_money(["0.10", "0.20"]) == Decimal("0.30")
    assert str(m.sum_money(["0.10", "0.20"])) == "0.30"
    assert m.sum_money(["1.005"]) == Decimal("1.01")
    assert str(m.sum_money([])) == "0.00"
