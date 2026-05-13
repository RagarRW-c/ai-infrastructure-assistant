import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

from app.prompts import InfraType

ValidationStatus = Literal["passed", "warning", "failed"]


class ValidationResult(BaseModel):
    status: ValidationStatus
    messages: list[str] = Field(default_factory=list)


def _result(messages: list[str], failed: bool = False) -> ValidationResult:
    if failed:
        return ValidationResult(status="failed", messages=messages)
    if messages:
        return ValidationResult(status="warning", messages=messages)
    return ValidationResult(status="passed", messages=["No validation issues found."])


def _is_latest_or_unpinned_image(image: str) -> bool:
    image_without_digest = image.split("@", 1)[0]
    tag = image_without_digest.rsplit(":", 1)

    if len(tag) == 1:
        return True

    return tag[1] == "latest"


def _contains_privileged_true(value: Any) -> bool:
    if isinstance(value, dict):
        if value.get("privileged") is True:
            return True
        return any(_contains_privileged_true(item) for item in value.values())

    if isinstance(value, list):
        return any(_contains_privileged_true(item) for item in value)

    return False


def _iter_kubernetes_containers(document: dict[str, Any]) -> list[dict[str, Any]]:
    template_spec = document.get("spec", {}).get("template", {}).get("spec", {})
    pod_spec = document.get("spec", {})

    containers = []
    for source in (template_spec, pod_spec):
        for key in ("containers", "initContainers"):
            items = source.get(key, [])
            if isinstance(items, list):
                containers.extend(item for item in items if isinstance(item, dict))

    return containers


def validate_kubernetes_output(code: str) -> ValidationResult:
    messages: list[str] = []

    try:
        documents = [doc for doc in yaml.safe_load_all(code) if doc is not None]
    except yaml.YAMLError as exc:
        return _result([f"Kubernetes YAML parsing failed: {exc}"], failed=True)

    if not documents:
        return _result(["Kubernetes output does not contain any YAML documents."], failed=True)

    for index, document in enumerate(documents, start=1):
        if not isinstance(document, dict):
            messages.append(f"Document {index} is not a YAML object.")
            continue

        api_version = document.get("apiVersion")
        kind = document.get("kind")
        if not api_version:
            messages.append(f"Document {index} is missing apiVersion.")
        if not kind:
            messages.append(f"Document {index} is missing kind.")

        if _contains_privileged_true(document):
            messages.append(f"Document {index} contains privileged: true.")

        for container in _iter_kubernetes_containers(document):
            name = container.get("name", "<unnamed>")
            image = container.get("image")
            if isinstance(image, str) and _is_latest_or_unpinned_image(image):
                messages.append(f"Container {name} uses an unpinned or latest image tag.")

            resources = container.get("resources", {})
            if (
                not isinstance(resources, dict)
                or not resources.get("requests")
                or not resources.get("limits")
            ):
                messages.append(f"Container {name} is missing resource requests or limits.")

            if kind in {"Deployment", "StatefulSet", "DaemonSet"}:
                if not container.get("readinessProbe"):
                    messages.append(f"Container {name} is missing readinessProbe.")
                if not container.get("livenessProbe"):
                    messages.append(f"Container {name} is missing livenessProbe.")

    failed = any(
        "missing apiVersion" in message or "missing kind" in message
        for message in messages
    )
    return _result(messages, failed=failed)


def _has_balanced_terraform_blocks(code: str) -> bool:
    braces = 0
    in_string = False
    escaped = False

    for char in code:
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_string:
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            braces += 1
        elif char == "}":
            braces -= 1
            if braces < 0:
                return False

    return braces == 0 and not in_string


def validate_terraform_output(code: str) -> ValidationResult:
    messages: list[str] = []
    failed = False

    if not _has_balanced_terraform_blocks(code):
        messages.append("Terraform appears to have unbalanced braces or unterminated strings.")
        failed = True

    if re.search(r'(?i)(password|secret|token|api_key)\s*=\s*"[^"$][^"]+"', code):
        messages.append("Terraform output appears to contain a hardcoded secret-like value.")

    terraform = shutil.which("terraform")
    if terraform:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "main.tf"
            path.write_text(code)
            completed = subprocess.run(
                [terraform, "fmt", "-check", "-no-color", str(path)],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            if completed.returncode != 0:
                output = (completed.stderr or completed.stdout).strip()
                suffix = f": {output}" if output else "."
                messages.append(f"terraform fmt -check failed{suffix}")

    return _result(messages, failed=failed)


def _dockerfile_base_image_is_unpinned(line: str) -> bool:
    parts = line.split()
    if len(parts) < 2:
        return False

    image = parts[1]
    if image.lower() == "scratch":
        return False

    return _is_latest_or_unpinned_image(image)


def validate_dockerfile_output(code: str) -> ValidationResult:
    messages: list[str] = []
    failed = False
    meaningful_lines = [
        line.strip()
        for line in code.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    from_lines = [line for line in meaningful_lines if line.upper().startswith("FROM ")]
    if not from_lines:
        messages.append("Dockerfile is missing a FROM instruction.")
        failed = True

    for line in from_lines:
        if _dockerfile_base_image_is_unpinned(line):
            messages.append(f"Base image is unpinned or uses latest tag: {line}")

    user_lines = [line for line in meaningful_lines if line.upper().startswith("USER ")]
    if not user_lines:
        messages.append("Dockerfile does not switch to a non-root USER.")
    elif user_lines[-1].split(maxsplit=1)[1] in {"0", "root"}:
        messages.append("Dockerfile final USER is root.")

    for line in meaningful_lines:
        if line.upper().startswith("ENV ") and re.search(
            r"(?i)(password|secret|token|api[_-]?key)", line
        ):
            messages.append("Dockerfile ENV appears to contain a secret-like variable.")

    hadolint = shutil.which("hadolint")
    if hadolint:
        completed = subprocess.run(
            [hadolint, "-"],
            input=code,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if completed.returncode != 0:
            output = (completed.stdout or completed.stderr).strip()
            messages.append(f"hadolint reported issues: {output}")

    return _result(messages, failed=failed)


def validate_generated_output(code: str, infra_type: InfraType) -> ValidationResult:
    if infra_type == "kubernetes":
        return validate_kubernetes_output(code)
    if infra_type == "terraform":
        return validate_terraform_output(code)
    if infra_type == "dockerfile":
        return validate_dockerfile_output(code)

    return ValidationResult(status="warning", messages=["No validator is available for this output type."])
