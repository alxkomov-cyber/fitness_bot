import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str
    ALLOWED_USER_ID: int
    DATABASE_URL: str
    GROQ_API_KEY: str
    LLM_API_KEY: str
    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODEL: str = "qwen/qwen3.8-27b"
    TIMEZONE: str = "Europe/Moscow"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

config = Settings()
