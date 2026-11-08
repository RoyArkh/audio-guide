import uuid

from fastapi.testclient import TestClient

from app import stories
from app.db import get_session
from app.main import app
from app.models import Job
from app.routers.stories import get_job_runner
from app.storage import LocalStorage, get_storage
from tests.fake_services import SCRIPT_REPLY, fake_services

PARIS = {"lat": 48.8556, "lng": 2.2986, "length": "short", "mood": "historical"}


def api_client(db_session, tmp_path, run_job) -> TestClient:
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_storage] = lambda: LocalStorage(tmp_path)
    app.dependency_overrides[get_job_runner] = lambda: run_job
    return TestClient(app)


def run_with_fakes(db_session, tmp_path):
    def run_job(job_id: uuid.UUID) -> None:
        stories.run_story(db_session, db_session.get(Job, job_id), fake_services(tmp_path))
    return run_job


def do_nothing(job_id: uuid.UUID) -> None:
    pass


def test_create_story_then_poll_until_done(db_session, tmp_path):
    client = api_client(db_session, tmp_path, run_with_fakes(db_session, tmp_path))

    created = client.post("/api/stories", json=PARIS)
    # The test client runs background tasks before returning, so the job is already finished.
    story = client.get(f"/api/stories/{created.json()['job_id']}")

    assert created.status_code == 202
    assert story.status_code == 200
    body = story.json()
    assert body["status"] == "done"
    assert body["place"] == {
        "name": "Eiffel Tower",
        "description": "Description of Eiffel Tower",
        "wikipedia_url": "https://en.wikipedia.org/?curid=1",
        "distance_m": 418,
        "at_place": False,
    }
    assert body["transcript"] == SCRIPT_REPLY
    assert body["audio_url"] == f"/api/media/audio/{body['job_id']}.mp3"
    assert body["duration_seconds"] == 1.0
    assert body["sources"][0]["title"] == "Eiffel Tower (Wikipedia)"
    assert body["error"] is None


def test_story_that_has_not_started_yet_is_pending(db_session, tmp_path):
    client = api_client(db_session, tmp_path, do_nothing)

    job_id = client.post("/api/stories", json=PARIS).json()["job_id"]
    body = client.get(f"/api/stories/{job_id}").json()

    assert body["status"] == "pending"
    assert (body["place"], body["transcript"], body["audio_url"]) == (None, None, None)
    assert body["sources"] == []


def test_create_story_is_refused_when_too_many_stories_are_unfinished(db_session, tmp_path, monkeypatch):
    client = api_client(db_session, tmp_path, do_nothing)
    monkeypatch.setattr(stories, "MAX_UNFINISHED_JOBS", stories.count_unfinished_jobs(db_session) + 1)

    first = client.post("/api/stories", json=PARIS)
    second = client.post("/api/stories", json=PARIS)

    assert first.status_code == 202
    assert second.status_code == 503


def test_create_story_rejects_invalid_input(db_session, tmp_path):
    client = api_client(db_session, tmp_path, do_nothing)

    assert client.post("/api/stories", json={**PARIS, "mood": "spooky"}).status_code == 422
    assert client.post("/api/stories", json={**PARIS, "lat": 91}).status_code == 422


def test_unknown_story_returns_404(db_session, tmp_path):
    response = api_client(db_session, tmp_path, do_nothing).get(f"/api/stories/{uuid.uuid4()}")

    assert response.status_code == 404


def test_malformed_story_id_returns_422(db_session, tmp_path):
    response = api_client(db_session, tmp_path, do_nothing).get("/api/stories/not-a-uuid")

    assert response.status_code == 422
