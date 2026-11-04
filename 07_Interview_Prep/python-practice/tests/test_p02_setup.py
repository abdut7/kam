from practice_target import load
import sys

import pytest

m = load("p02_setup")


def test_build_greeting():
    assert m.build_greeting("  Ada ") == "Hello, Ada!"
    assert m.build_greeting(greeting="Hi") == "Hi, there!"
    assert m.build_greeting("   ") == "Hello, there!"
    assert m.build_greeting("Bo", greeting="Hey", punctuation=".") == "Hey, Bo."
    with pytest.raises(TypeError):
        m.build_greeting("Bo", "Hey")  # greeting is keyword-only


def test_normalize_env():
    assert m.normalize_env(" PROD ") == "prod"
    assert m.normalize_env(None) == "dev"
    assert m.normalize_env("", default="staging") == "staging"
    with pytest.raises(ValueError):
        m.normalize_env("production")


def test_read_port():
    assert m.read_port({"PORT": "3000"}) == 3000
    assert m.read_port({}) == 8000
    assert m.read_port({"PORT": "  "}, default=9000) == 9000
    with pytest.raises(ValueError, match="80a0"):
        m.read_port({"PORT": "80a0"})
    with pytest.raises(ValueError, match="70000"):
        m.read_port({"PORT": "70000"})


def test_parse_args():
    assert m.parse_args(["build", "--env=prod", "--verbose", "--port", "8000"]) == {
        "_": ["build"],
        "env": "prod",
        "verbose": True,
        "port": "8000",
    }
    assert m.parse_args([]) == {"_": []}
    assert m.parse_args(["--dry-run", "--url=a=b", "x"]) == {"_": ["x"], "dry_run": True, "url": "a=b"}
    assert m.parse_args(["--name", "--shout"]) == {"_": [], "name": True, "shout": True}


def test_main_greets(capsys):
    assert m.main(["greet", "--name", "Ada"]) == 0
    assert capsys.readouterr().out.strip() == "Hello, Ada!"
    assert m.main(["greet", "--shout"]) == 0
    assert capsys.readouterr().out.strip() == "HELLO, THERE!"


def test_main_usage_and_sys_argv(capsys, monkeypatch):
    assert m.main([]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "usage: greet" in captured.err
    monkeypatch.setattr(sys, "argv", ["prog", "greet", "--name", "Lin"])
    assert m.main() == 0
    assert capsys.readouterr().out.strip() == "Hello, Lin!"
