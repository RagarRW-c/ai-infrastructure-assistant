from fastapi.testclient import TestClient

from app import main

client = TestClient(main.app)


def test_health_returns_runtime_metadata():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "model": main.settings.vertex_model,
        "location": main.settings.gcp_location,
    }


def test_generate_returns_model_result_with_validation(monkeypatch):
    def fake_generate_infra(prompt: str, infra_type: str, cloud: str) -> str:
        assert prompt == "Create nginx deployment"
        assert infra_type == "kubernetes"
        assert cloud == "gcp"
        return "apiVersion: v1\nkind: Service\nmetadata:\n  name: nginx"

    monkeypatch.setattr(main, "generate_infra", fake_generate_infra)

    response = client.post(
        "/generate",
        json={
            "prompt": "Create nginx deployment",
            "type": "kubernetes",
            "cloud": "gcp",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "result": "apiVersion: v1\nkind: Service\nmetadata:\n  name: nginx",
        "validation": {
            "status": "passed",
            "messages": ["No validation issues found."],
        },
    }


def test_generate_returns_validation_warnings(monkeypatch):
    def fake_generate_infra(prompt: str, infra_type: str, cloud: str) -> str:
        return "FROM node:latest\nCOPY . .\nCMD npm start"

    monkeypatch.setattr(main, "generate_infra", fake_generate_infra)

    response = client.post(
        "/generate",
        json={
            "prompt": "Create Dockerfile",
            "type": "dockerfile",
            "cloud": "aws",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"] == "FROM node:latest\nCOPY . .\nCMD npm start"
    assert payload["validation"]["status"] == "warning"
    assert "Base image is unpinned or uses latest tag: FROM node:latest" in payload["validation"]["messages"]
    assert "Dockerfile does not switch to a non-root USER." in payload["validation"]["messages"]


def test_generate_returns_failed_validation(monkeypatch):
    def fake_generate_infra(prompt: str, infra_type: str, cloud: str) -> str:
        return "kind: Service\nmetadata:\n  name: missing-api-version"

    monkeypatch.setattr(main, "generate_infra", fake_generate_infra)

    response = client.post(
        "/generate",
        json={
            "prompt": "Create service",
            "type": "kubernetes",
            "cloud": "gcp",
        },
    )

    assert response.status_code == 200
    assert response.json()["validation"] == {
        "status": "failed",
        "messages": ["Document 1 is missing apiVersion."],
    }


def test_generate_rejects_unsupported_type():
    response = client.post(
        "/generate",
        json={
            "prompt": "Create nginx deployment",
            "type": "ansible",
            "cloud": "gcp",
        },
    )

    assert response.status_code == 422


def test_generate_rejects_empty_prompt():
    response = client.post(
        "/generate",
        json={
            "prompt": "",
            "type": "kubernetes",
            "cloud": "gcp",
        },
    )

    assert response.status_code == 422


def test_generate_converts_unexpected_errors_to_http_500(monkeypatch):
    def fake_generate_infra(prompt: str, infra_type: str, cloud: str) -> str:
        raise RuntimeError("credentials missing")

    monkeypatch.setattr(main, "generate_infra", fake_generate_infra)

    response = client.post(
        "/generate",
        json={
            "prompt": "Create nginx deployment",
            "type": "kubernetes",
            "cloud": "gcp",
        },
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Infrastructure generation failed. Check backend logs for details."
    }
