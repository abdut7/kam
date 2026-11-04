"""Lesson 21 reference solutions: Python for FastAPI. A small todo API."""
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


def _get_or_404(store: dict[int, Todo], todo_id: int) -> Todo:
    todo = store.get(todo_id)
    if todo is None:
        # FastAPI catches HTTPException and sends {"detail": ...} with the status.
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@app.post("/todos", status_code=201)
def create_todo(body: TodoIn, store: Store) -> Todo:
    new_id = max(store, default=0) + 1  # max over a dict iterates its keys
    todo = Todo(id=new_id, **body.model_dump())
    store[new_id] = todo
    return todo


@app.get("/todos/{todo_id}")
def get_todo(todo_id: int, store: Store) -> Todo:
    return _get_or_404(store, todo_id)


@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int, store: Store) -> None:
    _get_or_404(store, todo_id)
    del store[todo_id]


@app.get("/todos")
def list_todos(
    store: Store,
    done: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Todo]:
    todos = [store[key] for key in sorted(store)]
    if done is not None:  # "is not None": done=False is a real filter value
        todos = [todo for todo in todos if todo.done == done]
    return todos[offset : offset + limit]  # slicing past the end is safe


@app.patch("/todos/{todo_id}")
def update_todo(todo_id: int, body: TodoPatch, store: Store) -> Todo:
    todo = _get_or_404(store, todo_id)
    # exclude_unset: only keys present in the JSON; exclude_none: ignore nulls.
    changes = body.model_dump(exclude_unset=True, exclude_none=True)
    # model_copy does not validate, which is safe here because TodoPatch
    # already validated every value in `changes`.
    updated = todo.model_copy(update=changes)
    store[todo_id] = updated
    return updated


@app.get("/export")
def export_titles(store: Store) -> StreamingResponse:
    async def lines() -> AsyncIterator[str]:
        for key in sorted(store):
            yield store[key].title + "\n"

    return StreamingResponse(lines(), media_type="text/plain")
