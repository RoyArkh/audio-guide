from fastapi.testclient import TestClient

from app import wikimedia
from app.db import get_session
from app.main import app
from app.models import Place
from tests.fake_wikimedia import failing_client, fake_client, wiki_page


def api_client(db_session, wikimedia_client) -> TestClient:
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[wikimedia.get_client] = lambda: wikimedia_client
    return TestClient(app)


def test_nearby_returns_best_place_and_saves_it(db_session):
    client = fake_client(
        [wiki_page(1, "Champ de Mars", 60, "Q217925"), wiki_page(2, "Eiffel Tower", 418, "Q243")],
        sitelinks={"Q217925": 57, "Q243": 191},
    )

    response = api_client(db_session, client).get("/api/places/nearby?lat=48.8556&lng=2.2986")

    assert response.status_code == 200
    body = response.json()
    assert body["place"]["name"] == "Eiffel Tower"
    assert body["place"]["at_place"] is False
    assert [c["name"] for c in body["runners_up"]] == ["Champ de Mars"]
    assert db_session.get(Place, body["place_id"]).wikidata_id == "Q243"


def test_nearby_returns_404_when_nothing_is_within_range(db_session):
    response = api_client(db_session, fake_client([])).get("/api/places/nearby?lat=30&lng=-40")

    assert response.status_code == 404


def test_nearby_returns_502_when_wikipedia_is_down(db_session):
    response = api_client(db_session, failing_client(503)).get("/api/places/nearby?lat=48.85&lng=2.29")

    assert response.status_code == 502


def test_nearby_rejects_out_of_range_coordinates(db_session):
    response = api_client(db_session, fake_client([])).get("/api/places/nearby?lat=91&lng=0")

    assert response.status_code == 422
