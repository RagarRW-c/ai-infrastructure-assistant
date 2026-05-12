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


def test_generate_returns_model_result(monkeypatch):
    def fake_generate_infra(prompt: str, infra_type: str, cloud: str) -> str:
        assert prompt == "Create nginx deployment"
        assert infra_type == "kubernetes"
        assert cloud == "gcp"
        return "apiVersion: apps/v1"

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
    assert response.json() == {"result": "apiVersion: apps/v1"}


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
