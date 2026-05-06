import vertexai

from vertexai.generative_models import GenerativeModel

vertexai.init(
    project="ai-infrastructure-assistant",
    location="europe-central2",
)

model = GenerativeModel("gemini-2.5-flash")


def generate_infra(
    prompt: str,
    infra_type: str,
    cloud: str
):

    full_prompt = f"""
You are a senior DevOps engineer.

Generate ONLY valid {infra_type} configuration for {cloud}.

Rules:
- production-ready
- secure defaults
- no markdown
- no explanations
- return only code

User request:
{prompt}
"""

    response = model.generate_content(full_prompt)

    return response.text