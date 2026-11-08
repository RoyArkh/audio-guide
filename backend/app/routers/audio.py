import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app import audio, tts
from app.schemas import AudioOut, AudioRequest
from app.storage import Storage, get_storage

log = logging.getLogger(__name__)

router = APIRouter(tags=["audio"])


@router.post("/audio", response_model=AudioOut)
def create_audio(
    body: AudioRequest,
    tts_provider: tts.TTSProvider = Depends(tts.get_tts),
    storage: Storage = Depends(get_storage),
):
    """Speak a script and save it as an MP3 (takes 10-60 s).

    A stand-in for the M4 job flow: paste in a script from POST /api/scripts.
    """
    try:
        result = audio.make_audio(tts_provider, body.text, body.mood)
    except (tts.TTSError, audio.AudioError) as exc:
        log.exception("Audio generation failed")
        raise HTTPException(status_code=502, detail=f"Audio generation failed: {exc}")

    key = f"audio/{uuid.uuid4().hex}.mp3"
    storage.save(key, result.mp3)
    return AudioOut(audio_url=storage.url(key), duration_seconds=result.duration_seconds, chunks=result.chunks)
