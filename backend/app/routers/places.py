import logging
from typing import Annotated

import httpx2
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import places, wikimedia
from app.db import get_session
from app.schemas import CandidateOut, NearbyPlacesOut

log = logging.getLogger(__name__)

router = APIRouter(tags=["places"])

RUNNERS_UP_SHOWN = 9


def find_and_save_candidates(
    session: Session, client: httpx2.Client, lat: float, lng: float,
) -> tuple[int, list[places.Candidate]]:
    """Candidates best first, and the saved best place's id. Raises 502 or 404."""
    try:
        candidates = places.find_candidates(client, lat, lng)
    except wikimedia.WikimediaError:
        log.exception("Place lookup failed for (%s, %s)", lat, lng)
        raise HTTPException(status_code=502, detail="Wikipedia lookup failed, try again shortly")

    if not candidates:
        raise HTTPException(status_code=404, detail=places.NO_PLACES_MESSAGE)

    place = places.save_place(session, candidates[0])
    session.commit()
    return place.id, candidates


@router.get("/places/nearby", response_model=NearbyPlacesOut)
def nearby_places(
    lat: Annotated[float, Query(ge=-90, le=90)],
    lng: Annotated[float, Query(ge=-180, le=180)],
    session: Session = Depends(get_session),
    client: httpx2.Client = Depends(wikimedia.get_client),
):
    """Find the best place to tell a story about, plus the runners-up for debugging."""
    place_id, candidates = find_and_save_candidates(session, client, lat, lng)
    best, *others = candidates

    return NearbyPlacesOut(
        place_id=place_id,
        place=CandidateOut.from_candidate(best),
        runners_up=[CandidateOut.from_candidate(c) for c in others[:RUNNERS_UP_SHOWN]],
    )
