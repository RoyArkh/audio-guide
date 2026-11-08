from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    app_env: str = "dev"
    # Wikimedia asks API clients to identify themselves with a contact URL.
    wikimedia_user_agent: str = "audioguide/0.1 (https://audioguide.royaarkh.com)"
    # Any OpenAI-compatible chat API: Gemini by default, or e.g. Ollama for local experiments.
    llm_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai"
    llm_model: str = "gemini-3.1-flash-lite"
    llm_api_key: str = ""
    # Gemini text-to-speech. Voices: https://ai.google.dev/gemini-api/docs/speech-generation
    tts_api_key: str = ""
    tts_model: str = "gemini-3.8-flash-lite-tts"
    tts_voice: str = "Sulafat"
    # Generated audio in dev (backend/media on the Mac), served at /api/media.
    media_dir: str = "media"


settings = Settings()
