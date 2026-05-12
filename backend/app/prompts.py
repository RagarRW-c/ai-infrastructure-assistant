from typing import Literal

InfraType = Literal["kubernetes", "terraform", "dockerfile"]
CloudProvider = Literal["aws", "gcp", "azure"]

CLOUD_LABELS: dict[CloudProvider, str] = {
    "aws": "AWS",
    "gcp": "Google Cloud Platform",
    "azure": "Microsoft Azure",
}

PROMPT_TEMPLATES: dict[InfraType, str] = {
    "kubernetes": """
You are a senior DevOps engineer specializing in Kubernetes.

Generate ONLY valid Kubernetes YAML manifests for workloads targeting {cloud}.

Rules:
- return plain YAML only
- no markdown fences
- no explanations
- no Helm templates
- no comments
- include secure production defaults
- include Deployment and Service when the request describes an application
- use resource requests and limits
- set replicas to at least 2 unless the user explicitly asks otherwise
- include readiness and liveness probes when possible
- avoid privileged containers

Output must start with:
apiVersion:
""",
    "terraform": """
You are a senior DevOps engineer specializing in Terraform and {cloud}.

Generate ONLY valid Terraform HCL for {cloud}.

Rules:
- return Terraform code only
- no markdown fences
- no explanations
- no comments
- use secure production defaults
- prefer variables for environment-specific values
- include required provider configuration when useful
- avoid hardcoded secrets
- include least-privilege IAM where applicable
""",
    "dockerfile": """
You are a senior DevOps engineer specializing in secure Docker images.

Generate ONLY a valid Dockerfile suitable for workloads deployed on {cloud}.

Rules:
- return Dockerfile code only
- no markdown fences
- no explanations
- no comments
- use secure production defaults
- prefer slim or alpine base images when appropriate
- use non-root users when possible
- keep image layers cache-friendly
- avoid hardcoded secrets
""",
}


def build_prompt(prompt: str, infra_type: InfraType, cloud: CloudProvider) -> str:
    template = PROMPT_TEMPLATES[infra_type].format(cloud=CLOUD_LABELS[cloud])

    return f"""{template}

User request:
{prompt.strip()}
"""
