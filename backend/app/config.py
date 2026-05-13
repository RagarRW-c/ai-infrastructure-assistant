import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    gcp_project: str = Field(default="ai-infrastructure-assistant")
    gcp_location: str = Field(default="europe-central2")
    vertex_model: str = Field(default="gemini-2.5-flash")
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "https://ai-infra-frontend-41844796013.europe-central2.run.app",
        ]
    )
    max_prompt_length: int = Field(default=4000, ge=100, le=20000)
    rate_limit_requests: int = Field(default=10, ge=0, le=1000)
    rate_limit_window_seconds: int = Field(default=60, ge=0, le=3600)


def _split_csv(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default

    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or default


@lru_cache
def get_settings() -> Settings:
    return Settings(
        gcp_project=os.getenv("GCP_PROJECT", "ai-infrastructure-assistant"),
        gcp_location=os.getenv("GCP_LOCATION", "europe-central2"),
        vertex_model=os.getenv("VERTEX_MODEL", "gemini-2.5-flash"),
        cors_origins=_split_csv(
            os.getenv("CORS_ORIGINS"),
            [
                "http://localhost:3000",
                "https://ai-infra-frontend-41844796013.europe-central2.run.app",
            ],
        ),
        max_prompt_length=int(os.getenv("MAX_PROMPT_LENGTH", "4000")),
        rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "10")),
        rate_limit_window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
    )
