import logging

import httpx2
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import llm, scripts, wikimedia
from app.db import get_session
from app.routers.places import find_and_save_candidates
from app.schemas import CandidateOut, ScriptOut, StoryRequest, SourceOut

log = logging.getLogger(__name__)

router = APIRouter(tags=["scripts"])

@router.post("/scripts", response_model=ScriptOut)
def create_script(
    body: StoryRequest,
    session: Session = Depends(get_session),
    wiki_client: httpx2.Client = Depends(wikimedia.get_client),
    llm_client: httpx2.Client = Depends(llm.get_client),
):
    """Find the best place nearby, research it and write a story script (takes 10-30 s).

    A synchronous stand-in for the M4 job flow, handy for trying out prompts.
    """
    place_id, candidates = find_and_save_candidates(session, wiki_client, body.lat, body.lng)
    best = candidates[0]
    page = best.page

    try:
        article_text = wikimedia.fetch_article_text(wiki_client, page.page_id)
    except wikimedia.WikimediaError:
        log.exception("Could not fetch the article for %r", page.title)
        raise HTTPException(status_code=502, detail="Wikipedia lookup failed, try again shortly")

    try:
        facts = scripts.extract_facts(llm_client, page, article_text)
        script = scripts.write_script(llm_client, best, facts, body.length, body.mood)
    except llm.LLMError as exc:
        log.exception("Script generation failed for %r", page.title)
        raise HTTPException(status_code=502, detail=f"Script generation failed: {exc}")

    return ScriptOut(
        place_id=place_id,
        place=CandidateOut.from_candidate(best),
        length=body.length,
        mood=body.mood,
        target_words=scripts.TARGET_WORDS[body.length],
        word_count=len(script.split()),
        script=script,
        facts=facts,
        sources=[SourceOut(**wikimedia.attribution(page))],
    )
