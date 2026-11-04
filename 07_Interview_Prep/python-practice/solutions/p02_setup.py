"""Lesson 2 reference solutions: setup, running code and tooling.

Run it as a script: uv run python solutions/p02_setup.py greet --name Ada --shout
"""

import sys
from collections.abc import Mapping

ALLOWED_ENVS = {"dev", "staging", "prod"}
USAGE = "usage: greet [--name NAME] [--shout]"


def build_greeting(name: str = "", *, greeting: str = "Hello", punctuation: str = "!") -> str:
    # `or` returns its first truthy operand, so an empty string falls through to "there".
    who = name.strip() or "there"
    return f"{greeting}, {who}{punctuation}"


def normalize_env(value: str | None, default: str = "dev") -> str:
    # After `if value is None: ...` the checker knows value is str below (type narrowing).
    if value is None or not value.strip():
        return default
    env = value.strip().lower()
    if env not in ALLOWED_ENVS:
        raise ValueError(f"APP_ENV must be one of {sorted(ALLOWED_ENVS)}, got {value!r}")
    return env


def read_port(env: Mapping[str, str], default: int = 8000) -> int:
    raw = env.get("PORT", "").strip()  # .get avoids KeyError when PORT is not set
    if not raw:
        return default
    try:
        port = int(raw)
    except ValueError:
        # `from None` hides the inner traceback; the message already says what is wrong.
        raise ValueError(f"PORT must be a whole number, got {raw!r}") from None
    if not 1 <= port <= 65535:  # chained comparison
        raise ValueError(f"PORT must be between 1 and 65535, got {raw!r}")
    return port


def parse_args(argv: list[str]) -> dict[str, object]:
    result: dict[str, object] = {"_": []}
    positional: list[str] = []
    i = 0
    while i < len(argv):
        item = argv[i]
        if item.startswith("--"):
            key, sep, value = item[2:].partition("=")  # partition splits once
            key = key.replace("-", "_")
            if sep:
                result[key] = value
            elif i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                result[key] = argv[i + 1]
                i += 1  # consume the value too
            else:
                result[key] = True
        else:
            positional.append(item)
        i += 1
    result["_"] = positional
    return result


def main(argv: list[str] | None = None) -> int:
    # Reading sys.argv here (not as a default value) keeps main() testable and current.
    args = parse_args(sys.argv[1:] if argv is None else argv)
    positional = args["_"]
    if not isinstance(positional, list) or not positional or positional[0] != "greet":
        print(USAGE, file=sys.stderr)
        return 2
    name = args.get("name")
    message = build_greeting(name if isinstance(name, str) else "")
    if args.get("shout") is True:
        message = message.upper()
    print(message)
    return 0


if __name__ == "__main__":
    # SystemExit(0) exits cleanly; any other int becomes the process exit code.
    raise SystemExit(main())
