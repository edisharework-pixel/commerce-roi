from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://commerce:commerce_dev@localhost:5433/commerce_roi"
    test_database_url: str = "sqlite+aiosqlite:///./test.db"
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    anthropic_api_key: str = ""  # Set via APP_ANTHROPIC_API_KEY env var

    model_config = {"env_prefix": "APP_"}


settings = Settings()
