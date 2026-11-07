"""Fake Wikipedia/Wikidata responses so tests don't depend on the network."""

import httpx2


def wiki_page(page_id: int, title: str, distance_m: float, wikidata_id: str | None = None,
              lat: float = 48.8584, lng: float = 2.2945) -> dict:
    page = {
        "pageid": page_id,
        "title": title,
        "description": f"Description of {title}",
        "coordinates": [{"lat": lat, "lon": lng, "dist": distance_m}],
    }
    if wikidata_id:
        page["pageprops"] = {"wikibase_item": wikidata_id}
    return page


def fake_client(pages: list[dict], sitelinks: dict[str, int] | None = None,
                article_text: str = "Article text.") -> httpx2.Client:
    sitelinks = sitelinks or {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        if request.url.params.get("prop") == "extracts":
            page = {"pageid": int(request.url.params["pageids"]), "extract": article_text}
            return httpx2.Response(200, json={"query": {"pages": [page]}})
        if request.url.host == "en.wikipedia.org":
            # Like the real API, an empty search has no "query" key at all.
            return httpx2.Response(200, json={"query": {"pages": pages}} if pages else {})
        ids = request.url.params["ids"].split("|")
        entities = {i: {"sitelinks": {f"wiki{n}": {} for n in range(sitelinks.get(i, 0))}} for i in ids}
        return httpx2.Response(200, json={"entities": entities})

    return httpx2.Client(transport=httpx2.MockTransport(handler))


def geosearch_client(pages: list[dict], searched_radii: list[int]) -> httpx2.Client:
    """Like the real GeoSearch, returns only the pages within the requested radius."""

    def handler(request: httpx2.Request) -> httpx2.Response:
        radius_m = int(request.url.params["ggsradius"])
        searched_radii.append(radius_m)
        found = [page for page in pages if page["coordinates"][0]["dist"] <= radius_m]
        return httpx2.Response(200, json={"query": {"pages": found}} if found else {})

    return httpx2.Client(transport=httpx2.MockTransport(handler))


def failing_client(status_code: int = 500, json: dict | None = None) -> httpx2.Client:
    return httpx2.Client(transport=httpx2.MockTransport(
        lambda request: httpx2.Response(status_code, json=json or {})
    ))
