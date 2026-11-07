from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    app_env: str = "dev"
    # Wikimedia asks API clients to identify themselves with a contact URL.
    wikimedia_user_agent: str = "audioguide/0.1 (https://audioguide.royaarkh.com)"


settings = Settings()
