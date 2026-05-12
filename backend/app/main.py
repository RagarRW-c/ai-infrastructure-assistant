from typing import Annotated

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.ai import InfrastructureGenerationError, generate_infra
from app.config import get_settings
from app.prompts import CloudProvider, InfraType

settings = get_settings()

app = FastAPI(
    title="AI Infrastructure Assistant API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials="*" not in settings.cors_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


class PromptRequest(BaseModel):
    prompt: Annotated[str, Field(min_length=1, max_length=settings.max_prompt_length)]
    type: InfraType
    cloud: CloudProvider


class GenerateResponse(BaseModel):
    result: str


class HealthResponse(BaseModel):
    status: str
    model: str
    location: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model=settings.vertex_model,
        location=settings.gcp_location,
    )


@app.post("/generate", response_model=GenerateResponse)
def generate(req: PromptRequest) -> GenerateResponse:
    try:
        result = generate_infra(req.prompt, req.type, req.cloud)
    except InfrastructureGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Infrastructure generation failed. Check backend logs for details.",
        ) from exc

    return GenerateResponse(result=result)
