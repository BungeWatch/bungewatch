from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized config, loaded from environment variables / .env.
    Nothing in the app should read os.environ directly — always go through this
    so there's one place that knows what config the app needs.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"

    database_url: str

    anthropic_api_key: str | None = None
    openai_api_key: str | None = None

    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "af-south-1"


settings = Settings()
