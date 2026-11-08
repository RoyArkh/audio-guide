import uuid

from pydantic import BaseModel, ConfigDict, Field

from app import places, wikimedia
from app.models import Job, JobStatus
from app.places import Candidate
from app.scripts import Length, Mood
from app.storage import Storage


class CandidateOut(BaseModel):
    name: str
    description: str | None
    wikidata_id: str | None
    wikipedia_url: str
    lat: float
    lng: float
    distance_m: int
    at_place: bool
    sitelinks: int
    score: float

    @classmethod
    def from_candidate(cls, candidate: Candidate) -> "CandidateOut":
        page = candidate.page
        return cls(
            name=page.title,
            description=page.description,
            wikidata_id=page.wikidata_id,
            wikipedia_url=wikimedia.wikipedia_url(page.page_id),
            lat=page.lat,
            lng=page.lng,
            distance_m=round(page.distance_m),
            at_place=candidate.at_place,
            sitelinks=candidate.sitelinks,
            score=round(candidate.score, 4),
        )


class NearbyPlacesOut(BaseModel):
    place_id: int
    place: CandidateOut
    runners_up: list[CandidateOut]


class StoryRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [{"lat": 48.8556, "lng": 2.2986, "length": "short", "mood": "historical"}],
    })

    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    length: Length
    mood: Mood


class SourceOut(BaseModel):
    title: str
    url: str
    license: str


class ScriptOut(BaseModel):
    place_id: int
    place: CandidateOut
    length: Length
    mood: Mood
    target_words: int
    word_count: int
    script: str
    facts: list[str]
    sources: list[SourceOut]


class AudioRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, json_schema_extra={
        "examples": [{"text": "Welcome to the Eiffel Tower.\n\nIt was built in 1889.", "mood": "historical"}],
    })

    text: str = Field(min_length=1, max_length=20_000)
    mood: Mood


class AudioOut(BaseModel):
    audio_url: str
    duration_seconds: float
    chunks: int


class StoryCreated(BaseModel):
    job_id: uuid.UUID


class StoryPlaceOut(BaseModel):
    name: str
    description: str | None
    wikipedia_url: str
    distance_m: int
    at_place: bool


class StoryOut(BaseModel):
    job_id: uuid.UUID
    status: JobStatus
    length: Length
    mood: Mood
    place: StoryPlaceOut | None
    transcript: str | None
    audio_url: str | None
    duration_seconds: float | None
    sources: list[SourceOut]
    error: str | None

    @classmethod
    def from_job(cls, job: Job, storage: Storage) -> "StoryOut":
        place = None
        if job.place is not None and job.distance_m is not None:
            place = StoryPlaceOut(
                name=job.place.name,
                description=job.place.description,
                wikipedia_url=wikimedia.wikipedia_url(job.place.wikipedia_page_id),
                distance_m=round(job.distance_m),
                at_place=places.is_at_place(job.distance_m),
            )
        episode = job.episode
        return cls(
            job_id=job.id,
            status=job.status,
            length=job.length,
            mood=job.mood,
            place=place,
            transcript=episode.script_text if episode else None,
            audio_url=storage.url(episode.audio_key) if episode else None,
            duration_seconds=episode.duration_seconds if episode else None,
            sources=episode.sources if episode else [],
            error=job.error,
        )
