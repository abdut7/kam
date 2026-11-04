"""Lesson 21: Python for FastAPI. A small todo API.

Run: uv run --with pytest --with fastapi --with httpx pytest tests/test_p21_fastapi.py

Done for you: the models, the store dependency, and every route's decorator and
signature (read them: they are the lesson). Your job: replace each
`raise NotImplementedError` with the handler body. Until you do, the handler
raises inside the request and TestClient re-raises the error in the test.
"""
from collections.abc import AsyncIterator, Iterator
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Todo API")


class TodoIn(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    done: bool = False


class Todo(TodoIn):
    id: int


class TodoPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    done: bool | None = None


_STORE: dict[int, Todo] = {}


def get_store() -> Iterator[dict[int, Todo]]:
    """A yield dependency. A real app opens a DB session before the yield and
    closes it after; this one hands out an in-memory dict. Tests override it."""
    yield _STORE


Store = Annotated[dict[int, Todo], Depends(get_store)]


@app.post("/todos", status_code=201)
def create_todo(body: TodoIn, store: Store) -> Todo:
    """Give the todo the next id (highest id in the store + 1, or 1 when the
    store is empty), save it in the store and return it.

    Example: POST /todos {"title": "buy milk"} -> 201 {"id": 1, "title": "buy milk", "done": false}
    """
    raise NotImplementedError


@app.get("/todos/{todo_id}")
def get_todo(todo_id: int, store: Store) -> Todo:
    """Return the todo, or raise HTTPException(status_code=404, detail="Todo not found").

    Example: GET /todos/99 on an empty store -> 404 {"detail": "Todo not found"}
    """
    raise NotImplementedError


@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int, store: Store) -> None:
    """Remove the todo and return None: FastAPI then sends 204 with an empty body.
    Raise 404 with detail "Todo not found" when it does not exist.

    Example: DELETE /todos/1 -> 204, then GET /todos/1 -> 404
    """
    raise NotImplementedError


@app.get("/todos")
def list_todos(
    store: Store,
    done: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Todo]:
    """Return todos in id order. When `done` is given, keep only the todos whose
    done flag matches it. Then skip `offset` items and return at most `limit`.

    Example: GET /todos?done=false&limit=2 -> the first two open todos
    """
    raise NotImplementedError


@app.patch("/todos/{todo_id}")
def update_todo(todo_id: int, body: TodoPatch, store: Store) -> Todo:
    """Change only the fields the client sent with a non-null value
    (body.model_dump(exclude_unset=True, exclude_none=True)), save and return
    the updated todo. Raise 404 with detail "Todo not found" when it is missing.

    Example: PATCH /todos/1 {"done": true} keeps the title and sets done to true
    """
    raise NotImplementedError


@app.get("/export")
def export_titles(store: Store) -> StreamingResponse:
    """Stream one title per line, in id order, with media type text/plain:
    define an async generator inside this function that yields "title\\n" for
    each todo, and return StreamingResponse(that_generator(), media_type="text/plain").

    Example: todos "buy milk" and "walk dog" -> body "buy milk\\nwalk dog\\n"
    """
    raise NotImplementedError
