"""Write a spoken story script in two LLM steps: list the facts in the
Wikipedia article, then write the script from those facts only."""

import logging
from enum import StrEnum

import httpx2

from app import llm
from app.places import Candidate
from app.wikimedia import WikiPage

log = logging.getLogger(__name__)

MAX_ARTICLE_CHARS = 60_000  # about 15k tokens; longer articles lose their last sections


class Length(StrEnum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class Mood(StrEnum):
    HISTORICAL = "historical"
    HISTORICAL_EMOTIONAL = "historical_emotional"
    ROMANTIC = "romantic"


# About 150 spoken words per minute: roughly 2, 5 and 10 minutes.
TARGET_WORDS = {Length.SHORT: 300, Length.MEDIUM: 750, Length.LONG: 1500}

MOOD_STYLES = {
    Mood.HISTORICAL: "Facts only. Calm and informative, no jokes.",
    Mood.HISTORICAL_EMOTIONAL: "History with fun facts, a few light jokes, and some deeper, moving moments.",
    Mood.ROMANTIC: "Fun facts and the romantic stories or legends linked to the place.",
}

FACTS_PROMPT = """You research places for an audio guide.
List the facts from the article that a tour guide could use: history, people, dates, numbers, fun facts, anecdotes, legends and folklore.
Rules:
- One fact per line, starting with "- ".
- Use only what the article says. Add nothing from your own knowledge.
- Start legends, folklore and unconfirmed stories with "Legend:".
- Most interesting facts first, at most 40.
- Output only the list."""

SCRIPT_PROMPT = """You write scripts for an audio guide. A text-to-speech voice reads them aloud to a visitor.
Rules:
- Only use facts from the fact list. Never invent dates, names or numbers.
- Present legends and folklore clearly as legends, e.g. "Legend has it...".
- Write for the ear: short sentences and natural transitions. No lists, headings or markdown.
- Talk to the listener directly, as "you".
- Output only the words to be spoken: no title, stage directions or sound effects.
- If there are too few facts for the target length, write a shorter script instead of padding or inventing."""


def extract_facts(client: httpx2.Client, page: WikiPage, article_text: str) -> list[str]:
    if len(article_text) > MAX_ARTICLE_CHARS:
        log.info("Article %r has %d characters, using the first %d", page.title, len(article_text), MAX_ARTICLE_CHARS)
        article_text = article_text[:MAX_ARTICLE_CHARS]

    reply = llm.chat(client, FACTS_PROMPT, f"Article: {page.title}\n\n{article_text}")
    facts = parse_facts(reply)
    if not facts:
        raise llm.LLMError(f"No facts in the LLM reply: {reply[:500]}")
    log.info("Extracted %d facts about %r", len(facts), page.title)
    return facts


def write_script(client: httpx2.Client, candidate: Candidate, facts: list[str], length: Length, mood: Mood) -> str:
    page = candidate.page
    target_words = TARGET_WORDS[length]
    if candidate.at_place:
        where = "At the place itself."
    else:
        where = f"About {describe_distance(page.distance_m)} away, not at the place itself. Say so briefly at the start."
    fact_lines = "\n".join(f"- {fact}" for fact in facts)

    prompt = (
        f"Place: {page.title}\n"
        f"Where the listener is: {where}\n"
        f"Style: {MOOD_STYLES[mood]}\n"
        f"Length: about {target_words} words.\n\n"
        f"Facts:\n{fact_lines}"
    )
    script = llm.chat(client, SCRIPT_PROMPT, prompt)
    log.info(
        "Wrote a %s/%s script about %r: %d words (target %d)",
        length, mood, page.title, len(script.split()), target_words,
    )
    return script


def parse_facts(reply: str) -> list[str]:
    """One fact per line; bullet markers and blank lines are dropped."""
    facts = []
    for line in reply.splitlines():
        fact = line.strip().lstrip("-*•").strip()
        if fact:
            facts.append(fact)
    return facts


def describe_distance(distance_m: float) -> str:
    if distance_m < 1000:
        return f"{round(distance_m / 50) * 50} metres"
    return f"{distance_m / 1000:.1f} kilometres"
