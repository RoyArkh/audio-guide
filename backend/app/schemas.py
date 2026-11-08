from pydantic import BaseModel, ConfigDict, Field

from app import wikimedia
from app.places import Candidate
from app.scripts import Length, Mood


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


class ScriptRequest(BaseModel):
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
