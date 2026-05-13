from app.validation import (
    validate_dockerfile_output,
    validate_kubernetes_output,
    validate_terraform_output,
)


def test_kubernetes_validator_passes_basic_service():
    result = validate_kubernetes_output(
        "apiVersion: v1\nkind: Service\nmetadata:\n  name: web\nspec:\n  selector:\n    app: web"
    )

    assert result.status == "passed"
    assert result.messages == ["No validation issues found."]


def test_kubernetes_validator_warns_about_container_best_practices():
    result = validate_kubernetes_output(
        """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  template:
    spec:
      containers:
        - name: web
          image: nginx:latest
          securityContext:
            privileged: true
"""
    )

    assert result.status == "warning"
    assert "Document 1 contains privileged: true." in result.messages
    assert "Container web uses an unpinned or latest image tag." in result.messages
    assert "Container web is missing resource requests or limits." in result.messages
    assert "Container web is missing readinessProbe." in result.messages
    assert "Container web is missing livenessProbe." in result.messages


def test_terraform_validator_fails_unbalanced_braces():
    result = validate_terraform_output('resource "aws_vpc" "main" {\n  cidr_block = "10.0.0.0/16"')

    assert result.status == "failed"
    assert "Terraform appears to have unbalanced braces or unterminated strings." in result.messages


def test_dockerfile_validator_fails_without_from():
    result = validate_dockerfile_output("RUN echo hello")

    assert result.status == "failed"
    assert "Dockerfile is missing a FROM instruction." in result.messages


def test_dockerfile_validator_warns_about_root_and_latest():
    result = validate_dockerfile_output("FROM python:latest\nCOPY . .\nUSER root")

    assert result.status == "warning"
    assert "Base image is unpinned or uses latest tag: FROM python:latest" in result.messages
    assert "Dockerfile final USER is root." in result.messages
