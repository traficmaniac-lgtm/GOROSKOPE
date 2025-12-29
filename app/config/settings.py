from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str = Field("", alias="BOT_TOKEN")
    use_openai: bool = Field(False, alias="USE_OPENAI")
    openai_api_key: str | None = Field(None, alias="OPENAI_API_KEY")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    db_path: str = Field("bot.db", alias="DB_PATH")
    free_quota: int = Field(3, alias="FREE_QUOTA")
    request_price_stars: int = Field(3, alias="REQUEST_PRICE_STARS")
    overrides_path: str = Field("bot_overrides.json", alias="OVERRIDES_PATH")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


settings = Settings()
