from practice_target import load

m = load("p16_idioms")


def test_safe_int():
    assert m.safe_int("42") == 42
    assert m.safe_int(" 7 ") == 7 and m.safe_int("-5") == -5
    assert m.safe_int("abc", -1) == -1
    assert m.safe_int(None) == 0


def test_index_of_max():
    assert m.index_of_max([3, 9, 2, 9]) == 1
    assert m.index_of_max([-4.5]) == 0
    assert m.index_of_max([-3, -1, -2]) == 1
    assert m.index_of_max([]) is None


def test_merge_settings():
    defaults = {"retries": 3, "debug": True, "name": "svc"}
    overrides = {"retries": 0, "debug": None, "name": "", "extra": False}
    merged = m.merge_settings(defaults, overrides)
    assert merged == {"retries": 0, "debug": True, "name": "", "extra": False}
    assert defaults == {"retries": 3, "debug": True, "name": "svc"}  # not mutated
    assert m.merge_settings({}, {}) == {}


def test_word_frequencies():
    assert m.word_frequencies("The cat. the hat!", 1) == [("the", 2)]
    text = "b a c a b -- ! d"
    assert m.word_frequencies(text, 3) == [("b", 2), ("a", 2), ("c", 1)]
    assert m.word_frequencies("", 5) == []
    assert m.word_frequencies("'Hi' hi, HI?", 2) == [("hi", 3)]


def test_rank_users():
    users = [
        {"name": "bo", "score": 5},
        {"name": "Al", "score": 5},
        {"name": "cy", "score": 9},
    ]
    snapshot = list(users)
    assert m.rank_users(users) == ["cy", "Al", "bo"]
    assert users == snapshot  # input order unchanged
    assert m.rank_users([]) == []


def test_files_by_suffix(tmp_path):
    (tmp_path / "pkg" / "sub").mkdir(parents=True)
    for rel in ["b.py", "a.PY", "notes.txt", "pkg/z.py", "pkg/c.py", "pkg/sub/d.py", "pkg/sub/e.md"]:
        (tmp_path / rel).write_text("x")
    (tmp_path / "folder.py").mkdir()  # a directory, not a file
    assert m.files_by_suffix(tmp_path, ".py") == {
        ".": ["a.PY", "b.py"],
        "pkg": ["c.py", "z.py"],
        "pkg/sub": ["d.py"],
    }
    assert m.files_by_suffix(tmp_path, ".csv") == {}
