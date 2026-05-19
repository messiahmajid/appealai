from pathlib import Path

from pydantic_settings import BaseSettings

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/appealai"
    anthropic_api_key: str = ""
    google_generative_ai_api_key: str = ""
    gemini_text_models: str = "gemini-2.0-flash-lite,gemini-2.5-flash-lite,gemini-2.5-flash"
    openrouter_api_key: str = ""
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": str(_ENV_FILE), "extra": "ignore"}


settings = Settings()
