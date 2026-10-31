import pytest
from fastapi.testclient import TestClient

from app.main import app

TEXT_V1 = "Customers can search products and pay by UPI.\nAdmin must manage stock."
TEXT_V2 = "Customers can search products and pay by UPI.\nAdmin must manage stock and view reports."


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("REQGENIE_DB", str(tmp_path / "test.db"))
    return TestClient(app)


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_create_update_and_version_history(client):
    created = client.post("/api/projects", json={"name": "Shop", "text": TEXT_V1})
    assert created.status_code == 200
    body = created.json()
    assert body["version"] == 1 and len(body["stories"]) == 3
    pid = body["project_id"]

    updated = client.post(f"/api/projects/{pid}/update", json={"text": TEXT_V2}).json()
    assert updated["version"] == 2
    assert updated["summary"]["modified"] == 1 and updated["summary"]["unchanged"] == 1

    versions = client.get(f"/api/projects/{pid}/versions").json()
    assert [v["version"] for v in versions] == [1, 2]
    old = client.get(f"/api/projects/{pid}/versions/1").json()
    assert len(old["stories"]) == 3
    assert client.get("/api/projects").json()[0]["latest_version"] == 2


def test_exports(client):
    pid = client.post("/api/projects", json={"name": "Shop", "text": TEXT_V1}).json()["project_id"]
    md = client.get(f"/api/projects/{pid}/export?format=md")
    assert md.status_code == 200 and "```mermaid" in md.text and "US-001" in md.text
    csv_resp = client.get(f"/api/projects/{pid}/export?format=csv")
    assert csv_resp.text.startswith("Summary,Issue Type,Priority,Description,Labels")


def test_errors(client):
    assert client.get("/api/projects/999/versions").status_code == 404
    assert client.post("/api/projects", json={"name": "x", "text": "hi"}).status_code == 422
    assert client.post("/api/projects", json={"name": "", "text": TEXT_V1}).status_code == 422


def test_front_end_is_served(client):
    page = client.get("/")
    assert page.status_code == 200 and "ReqGenie" in page.text
