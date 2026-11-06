"""Runs against the real dev database: `docker compose exec api pytest`."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_reports_database_and_extensions():
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["postgis"], "PostGIS extension is not enabled"
    assert body["pgvector"], "pgvector extension is not enabled"
