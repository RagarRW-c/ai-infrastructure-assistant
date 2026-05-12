import vertexai
from vertexai.generative_models import GenerativeModel

from app.config import get_settings
from app.prompts import CloudProvider, InfraType, build_prompt

_model: GenerativeModel | None = None


class InfrastructureGenerationError(RuntimeError):
    pass


def get_model() -> GenerativeModel:
    global _model

    if _model is None:
        settings = get_settings()
        vertexai.init(
            project=settings.gcp_project,
            location=settings.gcp_location,
        )
        _model = GenerativeModel(settings.vertex_model)

    return _model


def clean_generated_code(text: str) -> str:
    stripped = text.strip()

    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()

    return stripped


def generate_infra(prompt: str, infra_type: InfraType, cloud: CloudProvider) -> str:
    full_prompt = build_prompt(prompt, infra_type, cloud)
    response = get_model().generate_content(full_prompt)
    text = getattr(response, "text", "").strip()

    if not text:
        raise InfrastructureGenerationError("Model returned an empty response.")

    return clean_generated_code(text)
