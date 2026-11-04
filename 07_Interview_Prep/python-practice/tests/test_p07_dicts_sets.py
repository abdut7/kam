from practice_target import load

m = load("p07_dicts_sets")


def test_first_repeat():
    assert m.first_repeat(["a", "b", "c", "b", "a"]) == "b"
    assert m.first_repeat(["x", "x"]) == "x"
    assert m.first_repeat(["a", "b", "c"]) is None
    assert m.first_repeat([]) is None


def test_invert():
    assert m.invert({"a": "x", "b": "y", "c": "x"}) == {"x": ["a", "c"], "y": ["b"]}
    assert m.invert({}) == {}
    result = m.invert({"k": "v"})
    assert type(result) is dict
    assert list(m.invert({"b": "2", "a": "1", "c": "2"})) == ["2", "1"]


def test_set_report():
    assert m.set_report(["x", "y"], ["y", "z"]) == {
        "both": {"y"},
        "only_a": {"x"},
        "only_b": {"z"},
        "either_not_both": {"x", "z"},
    }
    r = m.set_report(["a", "a", "b"], [])
    assert r["both"] == set() and r["only_a"] == {"a", "b"}
    assert r["either_not_both"] == {"a", "b"}


def test_top_k_words():
    assert m.top_k_words("the cat and the hat", 2) == [("the", 2), ("cat", 1)]
    assert m.top_k_words("B b a A a", 1) == [("a", 3)]
    assert m.top_k_words("", 3) == []
    assert m.top_k_words("one two", 5) == [("one", 1), ("two", 1)]


def test_deep_merge():
    base = {"db": {"host": "a", "port": 5432}, "debug": False}
    override = {"db": {"host": "b"}, "debug": True}
    assert m.deep_merge(base, override) == {"db": {"host": "b", "port": 5432}, "debug": True}
    assert base == {"db": {"host": "a", "port": 5432}, "debug": False}  # not mutated
    assert m.deep_merge({"a": {"x": 1}}, {"a": 5}) == {"a": 5}
    assert m.deep_merge({}, {}) == {}


def test_lru_cache():
    c = m.LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1
    c.put("c", 3)  # evicts "b", the least recently used
    assert c.get("b") is None
    assert c.get("a") == 1 and c.get("c") == 3
    c.put("a", 10)  # update refreshes recency
    c.put("d", 4)  # evicts "c"
    assert c.get("c") is None and c.get("a") == 10
