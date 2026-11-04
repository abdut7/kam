import math

import pytest

from practice_target import load

m = load("p12_oop")


def test_bank_account_basics():
    acct = m.BankAccount("Asha", 100.0)
    assert acct.deposit(50.0) == 150.0
    assert acct.withdraw(30.0) == 120.0
    assert acct.balance == 120.0
    assert repr(acct) == "BankAccount(owner='Asha', balance=120.0)"


def test_bank_account_rules():
    acct = m.BankAccount("Ravi")
    with pytest.raises(ValueError):
        acct.withdraw(1.0)
    with pytest.raises(ValueError):
        acct.deposit(0)
    with pytest.raises(AttributeError):
        acct.balance = 1_000_000.0  # read-only property
    with pytest.raises(ValueError):
        m.BankAccount("Neg", -5.0)


def test_bank_account_class_attribute_and_classmethod():
    a = m.BankAccount.from_dict({"owner": "Imran", "balance": 10})
    b = m.BankAccount.from_dict({"owner": "Zoe"})
    assert (a.owner, a.balance, b.balance) == ("Imran", 10.0, 0.0)
    assert a.interest_rate == b.interest_rate == 0.02

    class Savings(m.BankAccount):
        interest_rate = 0.05

    s = Savings.from_dict({"owner": "Sam", "balance": 1})
    assert isinstance(s, Savings) and s.interest_rate == 0.05
    assert repr(s) == "Savings(owner='Sam', balance=1.0)"


def test_temperature():
    t = m.Temperature(100)
    assert t.fahrenheit == 212.0
    t.fahrenheit = 32
    assert t.celsius == 0.0
    with pytest.raises(ValueError):
        t.celsius = -300
    with pytest.raises(ValueError):
        m.Temperature(-274)


def test_money_equality_and_hashing():
    a = m.Money(1050, "INR")
    assert a == m.Money(1050, "INR")
    assert a != m.Money(1050, "USD")
    assert a != 1050
    assert len({a, m.Money(1050, "INR"), m.Money(1, "INR")}) == 2


def test_money_ordering_and_add():
    a, b = m.Money(500, "INR"), m.Money(1050, "INR")
    assert a < b and b >= a and a <= m.Money(500, "INR")
    assert sorted([b, a]) == [a, b]
    assert a + b == m.Money(1550, "INR")
    with pytest.raises(ValueError):
        a < m.Money(1, "USD")
    with pytest.raises(ValueError):
        a + m.Money(1, "USD")


def test_money_repr_str():
    assert repr(m.Money(1050, "INR")) == "Money(1050, 'INR')"
    assert str(m.Money(1050, "INR")) == "10.50 INR"
    assert str(m.Money(7, "USD")) == "0.07 USD"


def test_playlist_container_protocol():
    p = m.Playlist("Focus", ["Intro", "Deep Work"])
    p.add("Outro")
    assert len(p) == 3
    assert list(p) == ["Intro", "Deep Work", "Outro"]
    assert p[0] == "Intro" and p[-1] == "Outro" and p[1:] == ["Deep Work", "Outro"]
    assert "deep work" in p and "Missing" not in p


def test_playlist_does_not_share_lists():
    songs = ["A"]
    p1 = m.Playlist("one", songs)
    p1.add("B")
    assert songs == ["A"]  # caller's list untouched
    p2, p3 = m.Playlist("two"), m.Playlist("three")
    p2.add("X")
    assert len(p3) == 0 and not p3


def test_shapes_abstract_base_class():
    with pytest.raises(TypeError):
        m.Shape()
    assert m.Rectangle(2, 3).area() == 6
    assert math.isclose(m.Circle(1).area(), math.pi)
    assert m.Rectangle(2, 3).describe() == "Rectangle with area 6.00"
    assert m.Circle(2).describe() == "Circle with area 12.57"


def test_call_counter():
    @m.CallCounter
    def add(a, b=0):
        return a + b

    assert add(1, 2) == 3
    assert add(5, b=5) == 10
    assert add.calls == 2
    assert add.__name__ == "add"
    assert m.CallCounter(len).calls == 0
