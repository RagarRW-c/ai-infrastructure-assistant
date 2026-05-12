import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    gcp_project: str = Field(default="ai-infrastructure-assistant")
    gcp_location: str = Field(default="europe-central2")
    vertex_model: str = Field(default="gemini-2.5-flash")
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    max_prompt_length: int = Field(default=4000, ge=100, le=20000)


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
        cors_origins=_split_csv(os.getenv("CORS_ORIGINS"), ["http://localhost:3000"]),
        max_prompt_length=int(os.getenv("MAX_PROMPT_LENGTH", "4000")),
    )
