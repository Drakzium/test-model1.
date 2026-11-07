from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_ROOT / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "OBITO AI"
    secret_key: str = "dev-only-change-me"
    database_url: str = "sqlite:///./data/obito.db"
    session_days: int = 14
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    cookie_name: str = "obito_session"
    cookie_secure: bool = False
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_api_key: SecretStr = SecretStr("")
    llm_timeout_seconds: int = Field(default=90, ge=10, le=300)

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return Settings()
