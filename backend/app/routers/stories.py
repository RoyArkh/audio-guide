import logging
import uuid
from collections.abc import Callable

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app import stories
from app.db import get_session
from app.models import Job
from app.schemas import StoryCreated, StoryOut, StoryRequest
from app.storage import Storage, get_storage

log = logging.getLogger(__name__)

router = APIRouter(tags=["stories"])


def get_job_runner() -> Callable[[uuid.UUID], None]:
    """FastAPI dependency; tests override it to run jobs with fake services."""
    return stories.run_job


@router.post("/stories", status_code=202, response_model=StoryCreated)
def create_story(
    body: StoryRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    run_job: Callable[[uuid.UUID], None] = Depends(get_job_runner),
):
    """Start making a story. Poll GET /api/stories/{job_id} until the status is done or failed."""
    if stories.count_unfinished_jobs(session) >= stories.MAX_UNFINISHED_JOBS:
        raise HTTPException(status_code=503, detail="Busy with other stories, please try again in a minute")

    job = stories.create_job(session, body.lat, body.lng, body.length, body.mood)
    background_tasks.add_task(run_job, job.id)
    return StoryCreated(job_id=job.id)


@router.get("/stories/{job_id}", response_model=StoryOut)
def get_story(
    job_id: uuid.UUID,
    session: Session = Depends(get_session),
    storage: Storage = Depends(get_storage),
):
    job = session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Story not found")
    return StoryOut.from_job(job, storage)
