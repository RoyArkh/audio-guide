import pytest

from app import llm, scripts
from app.places import Candidate
from app.scripts import Length, Mood
from app.wikimedia import WikiPage
from tests.fake_llm import chat_response, fake_llm_client, user_prompt


def eiffel_tower(distance_m: float) -> Candidate:
    page = WikiPage(
        page_id=1, title="Eiffel Tower", description=None, wikidata_id="Q243",
        lat=48.8584, lng=2.2945, distance_m=distance_m,
    )
    return Candidate(page, sitelinks=191, score=1.0)


def test_parse_facts_drops_bullet_markers_and_blank_lines():
    reply = "- Built in 1889.\n\n* It is 330 m tall.\n• Legend: a ghost lives at the top.\n"

    assert scripts.parse_facts(reply) == [
        "Built in 1889.",
        "It is 330 m tall.",
        "Legend: a ghost lives at the top.",
    ]


def test_extract_facts_raises_when_the_reply_has_no_facts():
    client = fake_llm_client([chat_response("-\n-")])

    with pytest.raises(llm.LLMError, match="No facts"):
        scripts.extract_facts(client, eiffel_tower(10).page, "Some article text.")


def test_extract_facts_cuts_very_long_articles():
    requests = []
    client = fake_llm_client([chat_response("- A fact.")], requests)

    scripts.extract_facts(client, eiffel_tower(10).page, "x" * (scripts.MAX_ARTICLE_CHARS + 500))

    assert user_prompt(requests[0]).count("x") == scripts.MAX_ARTICLE_CHARS


def test_script_prompt_has_length_mood_and_facts():
    requests = []
    client = fake_llm_client([chat_response("Welcome to the Eiffel Tower.")], requests)

    script = scripts.write_script(client, eiffel_tower(10), ["Built in 1889."], Length.MEDIUM, Mood.ROMANTIC)

    assert script == "Welcome to the Eiffel Tower."
    prompt = user_prompt(requests[0])
    assert "At the place itself." in prompt
    assert "about 750 words" in prompt
    assert scripts.MOOD_STYLES[Mood.ROMANTIC] in prompt
    assert "- Built in 1889." in prompt


def test_script_prompt_mentions_the_distance_when_the_listener_is_not_at_the_place():
    requests = []
    client = fake_llm_client([chat_response("You're about 400 metres from the Eiffel Tower.")], requests)

    scripts.write_script(client, eiffel_tower(418), ["Built in 1889."], Length.SHORT, Mood.HISTORICAL)

    assert "About 400 metres away" in user_prompt(requests[0])


def test_describe_distance():
    assert scripts.describe_distance(418) == "400 metres"
    assert scripts.describe_distance(2963) == "3.0 kilometres"
