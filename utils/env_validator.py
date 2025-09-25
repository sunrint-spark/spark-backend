from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["settings"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, env_ignore_other_envs=True
    )
    MONGODB_URI: str
    MONGODB_DATABASE: str
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_API_KEY: str
    GOOGLE_SEARCH_ENGINE_ID: str
    OPENAI_API_KEY: str
    LIVEBLOCK_SECRET_KEY: str
    GOOGLE_REDIRECT_URI: str
    TEST_MODE: str = "false"


settings = Settings()