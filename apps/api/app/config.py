"""Application configuration."""

import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # OpAMP Server URL
    OPAMP_SERVER_URL: str = os.getenv("OPAMP_SERVER_URL", "http://localhost:4321")

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = True


settings = Settings()
