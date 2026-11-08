import httpx2

from app import stories
from app.models import Job, JobStatus
from app.scripts import Length, Mood
from tests.fake_services import SCRIPT_REPLY, fake_services
from tests.fake_tts import FailingTTS
from tests.fake_wikimedia import fake_client


class CrashingTTS:
    def synthesize(self, text: str, style: str) -> bytes:
        raise RuntimeError("internal details that shouldn't reach the listener")


def new_job(db_session) -> Job:
    return stories.create_job(db_session, 48.8556, 2.2986, Length.SHORT, Mood.ROMANTIC)


def test_successful_job_saves_an_episode_with_audio_and_sources(db_session, tmp_path):
    job = new_job(db_session)

    stories.run_story(db_session, job, fake_services(tmp_path))

    assert job.status == JobStatus.DONE
    assert job.error is None
    assert job.place.name == "Eiffel Tower"
    assert job.distance_m == 418
    episode = job.episode
    assert episode.script_text == SCRIPT_REPLY
    assert episode.facts == ["Built in 1889.", "It is 330 m tall."]
    assert episode.sources[0]["license"] == "CC BY-SA 4.0"
    assert (episode.length, episode.mood, episode.language) == ("short", "romantic", "en")
    assert episode.duration_seconds == 1.0
    assert (tmp_path / episode.audio_key).read_bytes().startswith(b"ID3")


def test_job_goes_through_every_stage_in_order(db_session, tmp_path, monkeypatch):
    statuses = []
    original_set_status = stories.set_status

    def recording_set_status(session, job, status):
        statuses.append(status)
        original_set_status(session, job, status)

    monkeypatch.setattr(stories, "set_status", recording_set_status)

    stories.run_story(db_session, new_job(db_session), fake_services(tmp_path))

    assert statuses == [
        JobStatus.FINDING_PLACE, JobStatus.RESEARCHING, JobStatus.WRITING,
        JobStatus.GENERATING_AUDIO, JobStatus.DONE,
    ]


def test_job_fails_when_no_place_is_nearby(db_session, tmp_path):
    job = new_job(db_session)

    stories.run_story(db_session, job, fake_services(tmp_path, wikipedia=fake_client([])))

    assert job.status == JobStatus.FAILED
    assert job.error == "No places found within 10 km"
    assert job.episode is None


def test_job_fails_with_the_reason_when_the_llm_fails(db_session, tmp_path):
    job = new_job(db_session)
    llm_error = httpx2.Response(400, json={"error": {"message": "API key not valid"}})

    stories.run_story(db_session, job, fake_services(tmp_path, llm_responses=[llm_error]))

    assert job.status == JobStatus.FAILED
    assert "API key not valid" in job.error
    assert job.place.name == "Eiffel Tower"


def test_job_fails_and_saves_no_audio_when_tts_fails(db_session, tmp_path):
    job = new_job(db_session)

    stories.run_story(db_session, job, fake_services(tmp_path, tts=FailingTTS()))

    assert job.status == JobStatus.FAILED
    assert "503" in job.error
    assert list(tmp_path.iterdir()) == []


def test_unexpected_errors_fail_the_job_without_showing_internal_details(db_session, tmp_path):
    job = new_job(db_session)

    stories.run_story(db_session, job, fake_services(tmp_path, tts=CrashingTTS()))

    assert job.status == JobStatus.FAILED
    assert job.error == stories.UNEXPECTED_ERROR_MESSAGE


def test_fail_interrupted_jobs_fails_only_unfinished_jobs(db_session):
    pending, writing, done = new_job(db_session), new_job(db_session), new_job(db_session)
    stories.set_status(db_session, writing, JobStatus.WRITING)
    stories.set_status(db_session, done, JobStatus.DONE)

    stories.fail_interrupted_jobs(db_session)
    db_session.expire_all()

    assert (pending.status, pending.error) == (JobStatus.FAILED, stories.INTERRUPTED_MESSAGE)
    assert writing.status == JobStatus.FAILED
    assert (done.status, done.error) == (JobStatus.DONE, None)
