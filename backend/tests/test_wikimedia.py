import httpx2
import pytest

from app import wikimedia
from tests.fake_wikimedia import failing_client, fake_client, wiki_page


def test_search_nearby_pages_sorts_by_distance_and_skips_pages_without_coordinates():
    no_coordinates = {"pageid": 3, "title": "Somewhere"}
    client = fake_client([
        wiki_page(1, "Far", 500, "Q1"),
        wiki_page(2, "Near", 50),
        no_coordinates,
    ])

    pages = wikimedia.search_nearby_pages(client, 48.85, 2.29, 2_000)

    assert [page.title for page in pages] == ["Near", "Far"]
    assert pages[0].wikidata_id is None
    assert pages[1].wikidata_id == "Q1"


def test_search_nearby_pages_returns_empty_list_when_nothing_is_nearby():
    assert wikimedia.search_nearby_pages(fake_client([]), 0.0, 0.0, 2_000) == []


def test_fetch_sitelink_counts_splits_large_requests_into_batches():
    requests = []

    def handler(request):
        ids = request.url.params["ids"].split("|")
        requests.append(ids)
        return httpx2.Response(200, json={"entities": {i: {"sitelinks": {"enwiki": {}}} for i in ids}})

    client = httpx2.Client(transport=httpx2.MockTransport(handler))
    ids = [f"Q{n}" for n in range(60)]

    counts = wikimedia.fetch_sitelink_counts(client, ids)

    assert [len(batch) for batch in requests] == [50, 10]
    assert counts == {i: 1 for i in ids}


def test_fetch_article_text_returns_the_plain_text():
    client = fake_client([], article_text="The Eiffel Tower is a tower.")

    assert wikimedia.fetch_article_text(client, 1) == "The Eiffel Tower is a tower."


def test_fetch_article_text_raises_when_the_page_has_no_text():
    client = failing_client(status_code=200, json={"query": {"pages": [{"pageid": 1, "missing": True}]}})

    with pytest.raises(wikimedia.WikimediaError, match="No article text"):
        wikimedia.fetch_article_text(client, 1)


def test_http_error_raises_wikimedia_error():
    with pytest.raises(wikimedia.WikimediaError):
        wikimedia.search_nearby_pages(failing_client(status_code=503), 48.85, 2.29, 2_000)


def test_api_error_in_response_body_raises_wikimedia_error():
    client = failing_client(status_code=200, json={"error": {"code": "badvalue", "info": "Bad coordinates"}})

    with pytest.raises(wikimedia.WikimediaError, match="Bad coordinates"):
        wikimedia.search_nearby_pages(client, 48.85, 2.29, 2_000)
