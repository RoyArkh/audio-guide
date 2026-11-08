"""Thin client for the Wikipedia and Wikidata APIs."""

import logging
from collections.abc import Iterator
from dataclasses import dataclass

import httpx2

from app.config import settings

log = logging.getLogger(__name__)

WIKI_LANG = "en"
WIKIPEDIA_API = f"https://{WIKI_LANG}.wikipedia.org/w/api.php"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"

MAX_SEARCH_RESULTS = 100
WIKIDATA_IDS_PER_REQUEST = 50  # wbgetentities limit


class WikimediaError(Exception):
    pass


@dataclass(frozen=True)
class WikiPage:
    page_id: int
    title: str
    description: str | None
    wikidata_id: str | None
    lat: float
    lng: float
    distance_m: float


def make_client() -> httpx2.Client:
    return httpx2.Client(
        headers={"User-Agent": settings.wikimedia_user_agent},
        timeout=10.0,
        transport=httpx2.HTTPTransport(retries=2),
    )


def get_client() -> Iterator[httpx2.Client]:
    """FastAPI dependency; tests override it with a mock client."""
    with make_client() as client:
        yield client


def search_nearby_pages(client: httpx2.Client, lat: float, lng: float, radius_m: int) -> list[WikiPage]:
    """Return the Wikipedia articles within radius_m of a point, closest first."""
    data = _get_json(client, WIKIPEDIA_API, {
        "action": "query",
        "generator": "geosearch",
        "ggscoord": f"{lat}|{lng}",
        "ggsradius": radius_m,
        "ggslimit": MAX_SEARCH_RESULTS,
        "prop": "coordinates|pageprops|description",
        "ppprop": "wikibase_item",
        "colimit": "max",
        "codistancefrompoint": f"{lat}|{lng}",
    })
    raw_pages = data.get("query", {}).get("pages", [])
    pages = [_parse_page(raw) for raw in raw_pages if raw.get("coordinates")]
    return sorted(pages, key=lambda page: page.distance_m)


def fetch_sitelink_counts(client: httpx2.Client, wikidata_ids: list[str]) -> dict[str, int]:
    """Number of Wikimedia sites (mostly language Wikipedias) with an article on each item."""
    counts = {}
    for start in range(0, len(wikidata_ids), WIKIDATA_IDS_PER_REQUEST):
        batch = wikidata_ids[start:start + WIKIDATA_IDS_PER_REQUEST]
        data = _get_json(client, WIKIDATA_API, {
            "action": "wbgetentities",
            "ids": "|".join(batch),
            "props": "sitelinks",
        })
        for wikidata_id, entity in data.get("entities", {}).items():
            counts[wikidata_id] = len(entity.get("sitelinks", {}))
    return counts


def fetch_article_text(client: httpx2.Client, page_id: int) -> str:
    """The whole article as plain text, with "== Section ==" headings."""
    data = _get_json(client, WIKIPEDIA_API, {
        "action": "query",
        "prop": "extracts",
        "explaintext": 1,
        "pageids": page_id,
    })
    pages = data.get("query", {}).get("pages", [])
    text = pages[0].get("extract") if pages else None
    if not text:
        raise WikimediaError(f"No article text for page {page_id}")
    return text


WIKIPEDIA_LICENSE = "CC BY-SA 4.0"


def attribution(page: WikiPage) -> dict:
    """Wikipedia text is CC BY-SA: stories based on it must credit the article."""
    return {"title": f"{page.title} (Wikipedia)", "url": wikipedia_url(page.page_id), "license": WIKIPEDIA_LICENSE}


def wikipedia_url(page_id: int) -> str:
    return f"https://{WIKI_LANG}.wikipedia.org/?curid={page_id}"


def _parse_page(raw: dict) -> WikiPage:
    coordinates = raw["coordinates"][0]
    return WikiPage(
        page_id=raw["pageid"],
        title=raw["title"],
        description=raw.get("description"),
        wikidata_id=raw.get("pageprops", {}).get("wikibase_item"),
        lat=coordinates["lat"],
        lng=coordinates["lon"],
        distance_m=coordinates["dist"],
    )


def _get_json(client: httpx2.Client, url: str, params: dict) -> dict:
    params = {**params, "format": "json", "formatversion": 2}
    try:
        response = client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    except (httpx2.HTTPError, ValueError) as exc:
        raise WikimediaError(f"Request to {url} failed: {exc}") from exc

    if "error" in data:
        raise WikimediaError(f"{url} returned an error: {data['error'].get('info')}")
    return data
