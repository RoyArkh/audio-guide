"""Story jobs: find a place, research it, write a script, speak it, and save the episode."""

import logging
import threading
import uuid
from dataclasses import dataclass

import httpx2
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app import audio, llm, places, scripts, tts, wikimedia
from app.db import SessionLocal
from app.models import Episode, Job, JobStatus
from app.scripts import Length, Mood
from app.storage import Storage, get_storage

log = logging.getLogger(__name__)

FINISHED_STATUSES = (JobStatus.DONE, JobStatus.FAILED)
MAX_UNFINISHED_JOBS = 5
UNEXPECTED_ERROR_MESSAGE = "Unexpected error, see the server logs"
INTERRUPTED_MESSAGE = "Interrupted by a server restart, please try again"

# A story takes a lot of memory and API quota, so only one is made at a time.
_one_story_at_a_time = threading.Lock()


class NoPlaceFound(Exception):
    pass


# Errors whose message is safe and useful to show to the listener.
KNOWN_ERRORS = (NoPlaceFound, wikimedia.WikimediaError, llm.LLMError, tts.TTSError, audio.AudioError)


@dataclass
class Services:
    """Everything a job talks to. Tests pass in fakes."""

    wikipedia: httpx2.Client
    llm: httpx2.Client
    tts: tts.TTSProvider
    storage: Storage


def create_job(session: Session, lat: float, lng: float, length: Length, mood: Mood) -> Job:
    job = Job(lat=lat, lng=lng, length=length, mood=mood, status=JobStatus.PENDING)
    session.add(job)
    session.commit()
    log.info("Job %s: created for (%.5f, %.5f), %s/%s", job.id, lat, lng, length, mood)
    return job


def count_unfinished_jobs(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(Job).where(Job.status.not_in(FINISHED_STATUSES)))


def fail_interrupted_jobs(session: Session) -> int:
    """Called at startup: jobs that were running when the server stopped will never finish.
    Assumes a single API process, as on the 1 GB server."""
    result = session.execute(
        update(Job)
        .where(Job.status.not_in(FINISHED_STATUSES))
        .values(status=JobStatus.FAILED, error=INTERRUPTED_MESSAGE)
    )
    session.commit()
    return result.rowcount


def run_job(job_id: uuid.UUID) -> None:
    """Background task: run one job with the real services."""
    with (
        _one_story_at_a_time,
        SessionLocal() as session,
        wikimedia.make_client() as wikipedia_client,
        llm.make_client() as llm_client,
        tts.make_client() as tts_client,
    ):
        job = session.get(Job, job_id)
        if job is None:
            log.error("Job %s: not found", job_id)
            return
        services = Services(wikipedia_client, llm_client, tts.GeminiTTS(tts_client), get_storage())
        run_story(session, job, services)


def run_story(session: Session, job: Job, services: Services) -> None:
    """Run every step, recording progress on the job. Never raises: failures end up in job.error."""
    try:
        job.episode = make_episode(session, job, services)
    except KNOWN_ERRORS as exc:
        fail(session, job, str(exc))
    except Exception:
        log.exception("Job %s: unexpected error while %s", job.id, job.status)
        fail(session, job, UNEXPECTED_ERROR_MESSAGE)
    else:
        set_status(session, job, JobStatus.DONE)


def make_episode(session: Session, job: Job, services: Services) -> Episode:
    length, mood = Length(job.length), Mood(job.mood)

    set_status(session, job, JobStatus.FINDING_PLACE)
    candidates = places.find_candidates(services.wikipedia, job.lat, job.lng)
    if not candidates:
        raise NoPlaceFound(places.NO_PLACES_MESSAGE)
    best = candidates[0]
    job.place = places.save_place(session, best)
    job.distance_m = best.page.distance_m

    set_status(session, job, JobStatus.RESEARCHING)
    article_text = wikimedia.fetch_article_text(services.wikipedia, best.page.page_id)
    facts = scripts.extract_facts(services.llm, best.page, article_text)

    set_status(session, job, JobStatus.WRITING)
    script = scripts.write_script(services.llm, best, facts, length, mood)

    set_status(session, job, JobStatus.GENERATING_AUDIO)
    result = audio.make_audio(services.tts, script, mood)
    audio_key = f"audio/{job.id}.mp3"
    services.storage.save(audio_key, result.mp3)

    episode = Episode(
        place=job.place,
        length=length,
        mood=mood,
        language=wikimedia.WIKI_LANG,
        script_text=script,
        facts=facts,
        sources=[wikimedia.attribution(best.page)],
        audio_key=audio_key,
        duration_seconds=result.duration_seconds,
    )
    session.add(episode)
    return episode


def set_status(session: Session, job: Job, status: JobStatus) -> None:
    job.status = status
    session.commit()
    log.info("Job %s: %s", job.id, status)


def fail(session: Session, job: Job, error: str) -> None:
    session.rollback()  # discard anything half-written by the failed step
    log.warning("Job %s: failed while %s: %s", job.id, job.status, error)
    job.status = JobStatus.FAILED
    job.error = error
    session.commit()
