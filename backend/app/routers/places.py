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


@router.get("/places/nearby", response_model=NearbyPlacesOut)
def nearby_places(
    lat: Annotated[float, Query(ge=-90, le=90)],
    lng: Annotated[float, Query(ge=-180, le=180)],
    session: Session = Depends(get_session),
    client: httpx2.Client = Depends(wikimedia.get_client),
):
    """Find the best place to tell a story about, plus the runners-up for debugging."""
    try:
        candidates = places.find_candidates(client, lat, lng)
    except wikimedia.WikimediaError:
        log.exception("Place lookup failed for (%s, %s)", lat, lng)
        raise HTTPException(status_code=502, detail="Wikipedia lookup failed, try again shortly")

    if not candidates:
        radius_km = places.SEARCH_RADII_M[-1] // 1000
        raise HTTPException(status_code=404, detail=f"No places found within {radius_km} km")

    best, *others = candidates
    place = places.save_place(session, best)
    session.commit()

    return NearbyPlacesOut(
        place_id=place.id,
        place=CandidateOut.from_candidate(best),
        runners_up=[CandidateOut.from_candidate(c) for c in others[:RUNNERS_UP_SHOWN]],
    )
