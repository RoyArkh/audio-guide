from pydantic import BaseModel

from app import wikimedia
from app.places import Candidate


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
