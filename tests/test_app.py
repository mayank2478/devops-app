import pytest

from app import create_app


@pytest.fixture()
def client(tmp_path):
    db_file = tmp_path / "test.db"
    app = create_app({"DATABASE_URL": f"sqlite:///{db_file}", "TESTING": True})
    with app.test_client() as client:
        yield client


def test_index_shows_app_info(client):
    res = client.get("/")
    assert res.status_code == 200
    body = res.get_json()
    assert body["app"] == "devops-demo"
    assert "version" in body
    assert "hostname" in body


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}


def test_ready_when_database_is_up(client):
    res = client.get("/ready")
    assert res.status_code == 200
    assert res.get_json()["database"] == "ok"


def test_create_and_list_tasks(client):
    res = client.post("/api/tasks", json={"title": "learn docker"})
    assert res.status_code == 201
    task = res.get_json()
    assert task["title"] == "learn docker"
    assert task["done"] is False

    res = client.get("/api/tasks")
    assert res.status_code == 200
    assert [t["title"] for t in res.get_json()] == ["learn docker"]


def test_create_task_requires_title(client):
    res = client.post("/api/tasks", json={"title": "   "})
    assert res.status_code == 400


def test_update_task(client):
    task_id = client.post("/api/tasks", json={"title": "write tests"}).get_json()["id"]
    res = client.patch(f"/api/tasks/{task_id}", json={"done": True})
    assert res.status_code == 200
    assert res.get_json()["done"] is True


def test_delete_task(client):
    task_id = client.post("/api/tasks", json={"title": "temp"}).get_json()["id"]
    assert client.delete(f"/api/tasks/{task_id}").status_code == 204
    assert client.delete(f"/api/tasks/{task_id}").status_code == 404


def test_starts_and_reports_not_ready_when_database_is_down():
    app = create_app({"DATABASE_URL": "postgresql+psycopg://u:p@127.0.0.1:5999/db"})
    with app.test_client() as client:
        assert client.get("/health").status_code == 200
        assert client.get("/ready").status_code == 503


def test_missing_task_returns_404(client):
    assert client.patch("/api/tasks/999", json={"done": True}).status_code == 404
