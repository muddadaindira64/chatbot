from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="ChatGPT Clone Backend", alias="APP_NAME")
    app_description: str = Field(
        default="Production-ready FastAPI foundation for the ChatGPT Clone backend.",
        alias="APP_DESCRIPTION",
    )
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    allowed_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="ALLOWED_ORIGINS",
    )
    sqlite_database_url: str = Field(
        default="sqlite:///./chatgpt_clone.db",
        alias="SQLITE_DATABASE_URL",
    )
    secret_key: str = Field(
        default="change-this-secret-key-to-a-secure-32-byte-key",
        alias="SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENROUTER_BASE_URL",
    )
    openrouter_model: str = Field(default="openai/gpt-oss-20b", alias="OPENROUTER_MODEL")

    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")
    @field_validator("debug", mode="before")
    @classmethod
    def normalize_debug_value(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "on"}:
                return True
            if normalized in {"false", "0", "no", "off", ""}:
                return False
        return False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
