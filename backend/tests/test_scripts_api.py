import httpx2
from fastapi.testclient import TestClient

from app import llm, wikimedia
from app.db import get_session
from app.main import app
from tests.fake_llm import chat_response, fake_llm_client
from tests.fake_wikimedia import eiffel_tower_wikipedia

PARIS = {"lat": 48.8556, "lng": 2.2986, "length": "short", "mood": "historical"}


def api_client(db_session, wikimedia_client, llm_client) -> TestClient:
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[wikimedia.get_client] = lambda: wikimedia_client
    app.dependency_overrides[llm.get_client] = lambda: llm_client
    return TestClient(app)


def test_create_script_returns_script_facts_and_sources(db_session):
    llm_api = fake_llm_client([
        chat_response("- Built in 1889.\n- It is 330 m tall."),
        chat_response("You're about 400 metres from the Eiffel Tower."),
    ])

    response = api_client(db_session, eiffel_tower_wikipedia(), llm_api).post("/api/scripts", json=PARIS)

    assert response.status_code == 200
    body = response.json()
    assert body["place"]["name"] == "Eiffel Tower"
    assert body["facts"] == ["Built in 1889.", "It is 330 m tall."]
    assert body["script"] == "You're about 400 metres from the Eiffel Tower."
    assert body["word_count"] == 8
    assert body["target_words"] == 300
    assert body["sources"][0]["url"] == "https://en.wikipedia.org/?curid=1"


def test_create_script_returns_502_with_the_reason_when_the_llm_fails(db_session):
    llm_api = fake_llm_client([httpx2.Response(400, json={"error": {"message": "API key not valid"}})])

    response = api_client(db_session, eiffel_tower_wikipedia(), llm_api).post("/api/scripts", json=PARIS)

    assert response.status_code == 502
    assert "API key not valid" in response.json()["detail"]


def test_create_script_rejects_unknown_mood(db_session):
    response = api_client(db_session, eiffel_tower_wikipedia(), fake_llm_client([])).post(
        "/api/scripts", json={**PARIS, "mood": "spooky"},
    )

    assert response.status_code == 422
