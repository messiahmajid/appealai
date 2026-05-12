from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/appealai"
    anthropic_api_key: str = ""
    google_generative_ai_api_key: str = ""
    openrouter_api_key: str = ""
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
