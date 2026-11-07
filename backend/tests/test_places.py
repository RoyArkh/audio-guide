from sqlalchemy import text

from app import places
from app.wikimedia import WikiPage
from tests.fake_wikimedia import geosearch_client, wiki_page


def page(title: str, distance_m: float, wikidata_id: str | None = None, page_id: int = 1) -> WikiPage:
    return WikiPage(
        page_id=page_id, title=title, description=None, wikidata_id=wikidata_id,
        lat=48.8584, lng=2.2945, distance_m=distance_m,
    )


def test_search_stops_at_2_km_when_something_is_there():
    searched_radii = []
    client = geosearch_client([wiki_page(1, "Café", 300), wiki_page(2, "Castle", 4_000)], searched_radii)

    pages = places.find_nearby_pages(client, 48.85, 2.29)

    assert searched_radii == [2_000]
    assert [p.title for p in pages] == ["Café"]


def test_search_widens_to_5_km_when_nothing_is_within_2_km():
    searched_radii = []
    client = geosearch_client([wiki_page(1, "Castle", 4_000)], searched_radii)

    pages = places.find_nearby_pages(client, 48.85, 2.29)

    assert searched_radii == [2_000, 5_000]
    assert [p.title for p in pages] == ["Castle"]


def test_search_gives_up_after_10_km():
    searched_radii = []
    client = geosearch_client([wiki_page(1, "Far Away Lighthouse", 12_000)], searched_radii)

    pages = places.find_nearby_pages(client, 48.85, 2.29)

    assert searched_radii == [2_000, 5_000, 10_000]
    assert pages == []


def test_famous_place_beats_closer_but_less_known_ones():
    # Real numbers from the Champ de Mars, Paris.
    pages = [
        page("Champ de Mars", 60, "Q217925"),
        page("Hôtel Pullman", 428, "Q106223086"),
        page("Eiffel Tower", 418, "Q243"),
    ]
    sitelinks = {"Q217925": 57, "Q106223086": 3, "Q243": 191}

    ranked = places.rank_candidates(pages, sitelinks)

    assert [c.page.title for c in ranked] == ["Eiffel Tower", "Champ de Mars", "Hôtel Pullman"]


def test_nearby_village_beats_famous_place_far_away():
    pages = [page("Big Castle", 8_000, "Q1"), page("Small Village", 300, "Q2")]

    ranked = places.rank_candidates(pages, {"Q1": 100, "Q2": 15})

    assert ranked[0].page.title == "Small Village"


def test_page_without_wikidata_counts_as_one_sitelink():
    ranked = places.rank_candidates([page("Local Pub", 100)], {})

    assert ranked[0].sitelinks == 1


def test_at_place_depends_on_distance():
    near, far = places.rank_candidates([page("Near", 100), page("Far", 900)], {})

    assert near.at_place is True
    assert far.at_place is False


def test_save_place_inserts_once_and_updates_on_repeat(db_session):
    first = places.save_place(db_session, places.Candidate(page("Eiffel Tower", 10, "Q243"), 190, 1.0))
    second = places.save_place(db_session, places.Candidate(page("Eiffel Tower", 10, "Q243"), 191, 1.0))

    assert second.id == first.id
    assert second.sitelinks == 191


def test_saved_location_has_latitude_and_longitude_the_right_way_round(db_session):
    saved = places.save_place(db_session, places.Candidate(page("Eiffel Tower", 10, "Q243"), 191, 1.0))

    lat, lng = db_session.execute(
        text("SELECT ST_Y(geom::geometry), ST_X(geom::geometry) FROM places WHERE id = :id"),
        {"id": saved.id},
    ).one()

    assert (round(lat, 4), round(lng, 4)) == (48.8584, 2.2945)
