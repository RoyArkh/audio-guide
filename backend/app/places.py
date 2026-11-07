"""Pick the most interesting place near a point and store it."""

import logging
from dataclasses import dataclass

import httpx2
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app import wikimedia
from app.models import Place
from app.wikimedia import WikiPage

log = logging.getLogger(__name__)

AT_PLACE_RADIUS_M = 250
SEARCH_RADII_M = [2_000, 5_000, 10_000]  # GeoSearch allows at most 10 km
# Added to the distance so that a place 10 m away doesn't beat a famous one
# 200 m away just because 10 is tiny. Larger values favour fame over closeness.
DISTANCE_OFFSET_M = 150


@dataclass(frozen=True)
class Candidate:
    page: WikiPage
    sitelinks: int
    score: float

    @property
    def at_place(self) -> bool:
        return self.page.distance_m <= AT_PLACE_RADIUS_M


def score(sitelinks: int, distance_m: float) -> float:
    """Fame divided by distance: a place twice as famous may be about twice as far away."""
    return sitelinks / (distance_m + DISTANCE_OFFSET_M)


def rank_candidates(pages: list[WikiPage], sitelink_counts: dict[str, int]) -> list[Candidate]:
    candidates = []
    for page in pages:
        # Pages without Wikidata data exist only on this Wikipedia.
        sitelinks = sitelink_counts.get(page.wikidata_id, 1)
        candidates.append(Candidate(page, sitelinks, score(sitelinks, page.distance_m)))
    return sorted(candidates, key=lambda candidate: candidate.score, reverse=True)


def find_nearby_pages(client: httpx2.Client, lat: float, lng: float) -> list[WikiPage]:
    """Search the smallest radius first and only widen it if nothing was found."""
    for radius_m in SEARCH_RADII_M:
        pages = wikimedia.search_nearby_pages(client, lat, lng, radius_m)
        log.info("(%.5f, %.5f): %d pages within %d m", lat, lng, len(pages), radius_m)
        if pages:
            return pages
    return []


def find_candidates(client: httpx2.Client, lat: float, lng: float) -> list[Candidate]:
    """Nearby places, best first. Empty if nothing is within the largest search radius."""
    pages = find_nearby_pages(client, lat, lng)
    wikidata_ids = [page.wikidata_id for page in pages if page.wikidata_id]
    sitelink_counts = wikimedia.fetch_sitelink_counts(client, wikidata_ids)
    candidates = rank_candidates(pages, sitelink_counts)

    if candidates:
        best = candidates[0]
        log.info(
            "(%.5f, %.5f): %d candidates, best %r at %d m with %d sitelinks",
            lat, lng, len(candidates), best.page.title, best.page.distance_m, best.sitelinks,
        )
    else:
        log.info("(%.5f, %.5f): no candidates", lat, lng)
    return candidates


def save_place(session: Session, candidate: Candidate) -> Place:
    """Insert the place, or refresh it if we've seen it before. Does not commit."""
    page = candidate.page
    values = {
        "name": page.title,
        "description": page.description,
        "wiki_lang": wikimedia.WIKI_LANG,
        "wikipedia_page_id": page.page_id,
        "wikidata_id": page.wikidata_id,
        "sitelinks": candidate.sitelinks,
        # WKT puts longitude first.
        "geom": f"SRID=4326;POINT({page.lng} {page.lat})",
    }
    statement = (
        insert(Place)
        .values(**values)
        .on_conflict_do_update(
            index_elements=["wiki_lang", "wikipedia_page_id"],
            set_={**values, "updated_at": func.now()},
        )
        .returning(Place)
        .execution_options(populate_existing=True)
    )
    return session.scalars(statement).one()
