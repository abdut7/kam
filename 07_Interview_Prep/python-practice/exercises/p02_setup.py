"""Lesson 2: setup, running code and tooling.

Replace each `raise NotImplementedError` with your code, then run from the python-practice folder:
    uv run --with pytest pytest tests/test_p02_setup.py

When it passes, try it as a real script too:
    uv run python exercises/p02_setup.py greet --name Ada --shout
"""

import sys
from collections.abc import Mapping


def build_greeting(name: str = "", *, greeting: str = "Hello", punctuation: str = "!") -> str:
    """Return "<greeting>, <name><punctuation>". A blank or whitespace-only name becomes "there".

    The name is stripped of surrounding spaces. greeting and punctuation are keyword-only
    (that is what the bare * in the signature means).

    Example: build_greeting("  Ada ") == "Hello, Ada!"; build_greeting(greeting="Hi") == "Hi, there!"
    """
    raise NotImplementedError


def normalize_env(value: str | None, default: str = "dev") -> str:
    """Normalise an APP_ENV value: strip spaces and lower-case it. None or blank gives default.

    Raise ValueError unless the result is one of "dev", "staging", "prod".
    A type checker flags value.strip() while value may still be None, so narrow it first.

    Example: normalize_env(" PROD ") == "prod"; normalize_env(None) == "dev"
    """
    raise NotImplementedError


def read_port(env: Mapping[str, str], default: int = 8000) -> int:
    """Read "PORT" from an environment mapping (shaped like os.environ) and return it as an int.

    Missing or blank PORT gives default. A value that is not a whole number, or is outside
    1..65535, raises ValueError whose message contains the bad value.

    Example: read_port({"PORT": "3000"}) == 3000; read_port({}) == 8000
    """
    raise NotImplementedError


def parse_args(argv: list[str]) -> dict[str, object]:
    """Parse command-line style arguments (like sys.argv[1:]) into a dict.

    - "--key=value" gives {"key": "value"} (split on the first "=" only)
    - "--key value" gives {"key": "value"} when the next item does not start with "--"
    - "--flag" with no value gives {"flag": True}
    - dashes inside keys become underscores: "--dry-run" gives the key "dry_run"
    - every other item is positional and is collected, in order, under "_" (always present)

    Example: parse_args(["build", "--env=prod", "--verbose", "--port", "8000"])
             == {"_": ["build"], "env": "prod", "verbose": True, "port": "8000"}
    """
    raise NotImplementedError


def main(argv: list[str] | None = None) -> int:
    """Entry point for a tiny CLI: greet [--name NAME] [--shout]

    - When argv is None, read sys.argv[1:] at call time.
    - If the first positional argument is "greet", print build_greeting(name) to stdout
      (upper-cased with --shout) and return 0. A missing or valueless --name means no name.
    - Otherwise print "usage: greet [--name NAME] [--shout]" to stderr and return 2.

    Example: main(["greet", "--name", "Ada"]) prints "Hello, Ada!" and returns 0
    """
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
