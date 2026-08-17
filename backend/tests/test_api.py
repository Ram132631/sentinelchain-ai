import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    # TestClient must be used as a context manager for startup/shutdown
    # (lifespan) events -- including our init_db()/demo-repo seeding -- to run.
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["demo_mode_available"] is True


def test_demo_repository_is_seeded_on_startup(client):
    resp = client.get("/api/repositories")
    assert resp.status_code == 200
    repos = resp.json()
    assert any(r["is_demo"] for r in repos)


def test_create_repository_rejects_invalid_url(client):
    resp = client.post("/api/repositories", json={"url": "not-a-github-url"})
    assert resp.status_code == 400


def test_create_repository_accepts_valid_github_url(client):
    resp = client.post("/api/repositories", json={"url": "https://github.com/octocat/Hello-World"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["full_name"] == "octocat/Hello-World"
    assert body["status"] == "UNSCANNED"


def test_vulnerability_not_found_returns_404(client):
    resp = client.get("/api/vulnerabilities/does-not-exist")
    assert resp.status_code == 404


def test_dashboard_summary_returns_shape(client):
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert "critical_vulnerabilities" in body
    assert "severity_distribution" in body
