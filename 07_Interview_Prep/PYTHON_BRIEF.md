# Brief: the Python tab (read fully)

You are writing part of a new "Python" tab in an interview-prep study page, plus matching practice files. Read `CONTENT_FORMAT.md` in this folder first (block types, "Architecture blocks", "Scenario-first rules").

## The learner
An experienced JavaScript and TypeScript engineer (Node.js, Express, NestJS, React) who says: "I have to learn Python very basically... every concept, every pattern, everything about Python coding... I have to practice... Python basics and advanced, compared with the FastAPI things." He knows programming well, so never explain what a loop or a variable is in general; explain how Python does it, why, and how it differs from JavaScript. Start each topic truly simple, then go deep. Use Python 3.12 syntax (note when something needs 3.10+ or 3.11+).

## Each section (your task lists the exact titles), in this order
1. framing blockquote: what this topic covers and where it shows up in real FastAPI and AI backend code.
2. `### Why it exists` : 3-5 sentences: the problem this feature solves or why Python does it this way.
3. `### In plain words` : 4-6 very simple sentences with an analogy.
4. Two or three `### Walkthrough: <title>` lessons. Numbered steps, each with a short code example in a ```python fence, and a JavaScript comparison where it helps (```js fence or an inline mention). These are the main teaching blocks: cover every important concept of the topic, including the traps.
5. `### Concepts you must understand` : 6-10 bullets with the rules to remember, then a GFM table "JavaScript" | "Python" | "Note" with 6-12 rows for this topic.
6. Five or six `### Q. ` exercises. Titles are tasks, never "What is": "Write a function that...", "Predict the output of this code and explain it.", "This function returns the wrong result for an empty list. Find and fix the bug.", "Rewrite this JavaScript in idiomatic Python.", "Refactor this code to use a generator.". Put any code the task needs in the Deeper explanation's first lines if it must be shown. Use the four labels this way: **Short answer (45 seconds):** the approach in 2-3 sentences; **Deeper explanation:** the full solution in a ```python fence, then why it works, edge cases and complexity where relevant; **Follow-ups they will ask:** 2-3 variations; **Mistakes to avoid:** 1-3 common bugs. 150-420 words each.
7. `### Practice` : first bullet exactly: "Practice kit: open `python-practice/exercises/<file>.py`, implement each function, then run `uv run --with pytest pytest tests/test_<file>.py` from the `python-practice` folder." Then 2-3 more small exercises to try in the REPL.

## Practice kit files (for every section you write)
In `/Users/abdurahman/Desktop/Kam h/07_Interview_Prep/python-practice/` (read its README.md):
- `exercises/<file>.py` : 4-6 functions (or a small class) with type hints and a docstring stating the task and one example; the body is `raise NotImplementedError`. Order them easy to hard.
- `solutions/<file>.py` : the same names, working, idiomatic, commented where helpful.
- `tests/test_<file>.py` : starts with `from practice_target import load` and `m = load("<file>")`, then pytest tests (2-4 asserts per function, including an edge case). For async functions use `asyncio.run(...)` inside a normal test; do not require pytest-asyncio. Only the FastAPI lessons may import `fastapi` (tests may use `fastapi.testclient.TestClient`, which needs httpx).
- Verify before you finish, from the `python-practice` folder: `PRACTICE_TARGET=solutions uv run --with pytest pytest tests/test_<file>.py` must pass (add `--with fastapi --with httpx` for FastAPI lessons), and running without PRACTICE_TARGET must fail with NotImplementedError. Fix anything that does not. Delete any `__pycache__` or `.pytest_cache` you create.

## Rules
- No em or en dashes, no HTML, straight quotes, every code fence tagged.
- Code must be correct; run anything you are unsure of with `python3 -c` or `uv run python`. Do not browse.
- Do not touch files other than your own content file and your own practice files.
- Run `node build/validate.mjs content/<your file>` from the `07_Interview_Prep` folder and fix what it flags.
- Report back only: paths, sections, exercise counts, kit test results (pass count against solutions), anything left out.
