import logging
import time
from typing import Annotated

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.ai import InfrastructureGenerationError, generate_infra
from app.config import get_settings
from app.prompts import CloudProvider, InfraType
from app.rate_limit import RateLimiter, get_client_identifier
from app.validation import ValidationResult, validate_generated_output

settings = get_settings()
logger = logging.getLogger(__name__)
generate_rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)

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
    validation: ValidationResult


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
def generate(req: PromptRequest, request: Request) -> GenerateResponse:
    client_id = get_client_identifier(request)
    allowed, retry_after = generate_rate_limiter.check(client_id)
    if not allowed:
        logger.warning(
            "generate rate limit exceeded client=%s retry_after=%s",
            client_id,
            retry_after,
        )
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    start_time = time.perf_counter()
    try:
        result = generate_infra(req.prompt, req.type, req.cloud)
        validation = validate_generated_output(result, req.type)
    except InfrastructureGenerationError as exc:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.warning(
            "generate model error client=%s type=%s cloud=%s prompt_length=%s duration_ms=%s error=%s",
            client_id,
            req.type,
            req.cloud,
            len(req.prompt),
            duration_ms,
            exc,
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.exception(
            "generate failed client=%s type=%s cloud=%s prompt_length=%s duration_ms=%s",
            client_id,
            req.type,
            req.cloud,
            len(req.prompt),
            duration_ms,
        )
        raise HTTPException(
            status_code=500,
            detail="Infrastructure generation failed. Check backend logs for details.",
        ) from exc

    duration_ms = int((time.perf_counter() - start_time) * 1000)
    logger.info(
        "generate completed client=%s type=%s cloud=%s prompt_length=%s validation_status=%s duration_ms=%s",
        client_id,
        req.type,
        req.cloud,
        len(req.prompt),
        validation.status,
        duration_ms,
    )
    return GenerateResponse(result=result, validation=validation)
