import httpx2

from app.stories import Services
from app.storage import LocalStorage
from app.tts import TTSProvider
from tests.fake_llm import chat_response, fake_llm_client
from tests.fake_tts import FakeTTS
from tests.fake_wikimedia import eiffel_tower_wikipedia

FACTS_REPLY = "- Built in 1889.\n- It is 330 m tall."
SCRIPT_REPLY = "You're about 400 metres from the Eiffel Tower.\n\nIt was built in 1889."


def fake_services(storage_folder, wikipedia: httpx2.Client | None = None,
                  llm_responses: list[httpx2.Response] | None = None,
                  tts: TTSProvider | None = None) -> Services:
    """By default: the Eiffel Tower is nearby and every step succeeds."""
    if llm_responses is None:
        llm_responses = [chat_response(FACTS_REPLY), chat_response(SCRIPT_REPLY)]
    return Services(
        wikipedia=wikipedia or eiffel_tower_wikipedia(),
        llm=fake_llm_client(llm_responses),
        tts=tts or FakeTTS(),
        storage=LocalStorage(storage_folder),
    )
