"""Application configuration."""

import os

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    # OpAMP Server URL
    OPAMP_SERVER_URL: str = os.getenv("OPAMP_SERVER_URL", "http://localhost:4321")


settings = Settings()
