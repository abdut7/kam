# Python practice kit

Each lesson in the atlas's Python tab has a matching exercise file here. You fill in the functions; the tests tell you when they work.

## One-time setup
`uv` is already installed on this Mac. Nothing else is needed: the commands below fetch pytest (and FastAPI for the last lessons) on the fly.

## Daily loop
1. Open an exercise file, for example `exercises/p06_lists_tuples.py`. Each function has a docstring that says what to build and an example.
2. Replace `raise NotImplementedError` with your code.
3. Run that lesson's tests from this folder:

```bash
uv run --with pytest pytest tests/test_p06_lists_tuples.py
```

4. Green dots mean pass. Red output shows the expected value and what your code returned.
5. Stuck for more than 20 minutes? Read the matching file in `solutions/`, close it, and write it again from memory.

## Run everything
```bash
uv run --with pytest --with fastapi --with httpx pytest
```

## Check the reference solutions pass
```bash
PRACTICE_TARGET=solutions uv run --with pytest --with fastapi --with httpx pytest
```

## Files
- `exercises/` : your work. Function stubs with docstrings.
- `solutions/` : reference answers, same function names.
- `tests/` : pytest tests, one file per lesson.
