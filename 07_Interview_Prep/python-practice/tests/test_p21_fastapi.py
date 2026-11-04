from practice_target import load

import warnings

import pytest

pytest.importorskip("fastapi", reason="run with: --with fastapi --with httpx")
with warnings.catch_warnings():
    # Newer Starlette releases suggest httpx2 for the test client; httpx still works.
    warnings.simplefilter("ignore")
    from fastapi.testclient import TestClient

m = load("p21_fastapi")


@pytest.fixture
def store():
    return {}


@pytest.fixture
def seeded(store):
    titles = ["buy milk", "walk dog", "write tests", "ship it", "rest"]
    for todo_id, title in enumerate(titles, start=1):
        store[todo_id] = m.Todo(id=todo_id, title=title, done=todo_id % 2 == 0)
    return store


@pytest.fixture
def client(store):
    # dependency_overrides swaps get_store for a fresh dict in every test.
    m.app.dependency_overrides[m.get_store] = lambda: store
    with TestClient(m.app) as test_client:  # `with` also runs lifespan events
        yield test_client
    m.app.dependency_overrides.clear()


def test_create_assigns_ids_and_validates(client, store):
    r = client.post("/todos", json={"title": "buy milk"})
    assert (r.status_code, r.json()) == (201, {"id": 1, "title": "buy milk", "done": False})
    assert client.post("/todos", json={"title": "walk dog", "done": True}).json()["id"] == 2
    assert client.post("/todos", json={"title": ""}).status_code == 422
    assert sorted(store) == [1, 2]


def test_get_todo(client, seeded):
    r = client.get("/todos/2")
    assert r.json() == {"id": 2, "title": "walk dog", "done": True}
    assert client.get("/todos/abc").status_code == 422  # path param must be an int


def test_get_missing_todo_is_404(client):
    r = client.get("/todos/99")
    assert (r.status_code, r.json()) == (404, {"detail": "Todo not found"})


def test_delete_todo(client, seeded):
    r = client.delete("/todos/1")
    assert (r.status_code, r.content) == (204, b"")
    assert 1 not in seeded
    assert client.delete("/todos/1").status_code == 404


def test_list_filters_and_paginates(client, seeded):
    ids = lambda r: [todo["id"] for todo in r.json()]
    assert ids(client.get("/todos")) == [1, 2, 3, 4, 5]
    assert ids(client.get("/todos", params={"done": "true"})) == [2, 4]
    assert ids(client.get("/todos", params={"done": "false", "limit": 2, "offset": 1})) == [3, 5]
    assert client.get("/todos", params={"limit": 0}).status_code == 422


def test_list_empty_store(client):
    r = client.get("/todos")
    assert (r.status_code, r.json()) == (200, [])


def test_patch_changes_only_sent_fields(client, seeded):
    r = client.patch("/todos/1", json={"done": True})
    assert r.json() == {"id": 1, "title": "buy milk", "done": True}
    assert client.patch("/todos/1", json={"title": None}).json()["title"] == "buy milk"
    assert seeded[1].done is True
    assert client.patch("/todos/1", json={"title": ""}).status_code == 422


def test_patch_missing_todo_is_404(client):
    assert client.patch("/todos/7", json={"done": True}).status_code == 404


def test_export_streams_titles(client, store):
    store[2] = m.Todo(id=2, title="walk dog")
    store[1] = m.Todo(id=1, title="buy milk")
    r = client.get("/export")
    assert r.text == "buy milk\nwalk dog\n"
    assert r.headers["content-type"].startswith("text/plain")


def test_export_empty_store(client):
    assert client.get("/export").text == ""
