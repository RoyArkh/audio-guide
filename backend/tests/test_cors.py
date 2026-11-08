from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_expo_dev_server_may_call_the_api():
    response = client.get("/api/health", headers={"Origin": "http://localhost:8081"})

    assert response.headers["access-control-allow-origin"] == "http://localhost:8081"


def test_other_sites_may_not_call_the_api():
    response = client.get("/api/health", headers={"Origin": "https://example.com"})

    assert "access-control-allow-origin" not in response.headers
