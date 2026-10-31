from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str = Field(default="CHANGE_ME")
    admin_ids: str = ""

    api_football_key: str = ""
    thesportsdb_key: str = "123"
    odds_api_key: str = ""

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2"
    use_mock_llm: bool = False

    value_edge_threshold: float = 0.05
    scheduler_interval_minutes: int = 10
    prematch_hours_before: int = 1

    google_sheets_credentials: str = ""
    google_sheets_spreadsheet: str = ""

    database_url: str = "sqlite+aiosqlite:///./data/bot.db"
    log_level: str = "INFO"
    request_rps: float = 2.0

    @property
    def admin_id_list(self) -> list[int]:
        if not self.admin_ids.strip():
            return []
        return [int(x.strip()) for x in self.admin_ids.split(",") if x.strip()]

    @property
    def has_api_football(self) -> bool:
        return bool(self.api_football_key.strip())

    @property
    def has_odds_api(self) -> bool:
        return bool(self.odds_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return Settings()


settings = get_settings()
