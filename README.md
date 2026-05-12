# AI Infrastructure Assistant

AI Infrastructure Assistant is a small full-stack app for generating infrastructure snippets from natural language prompts. The frontend lets a user choose an output type and cloud provider, then the FastAPI backend calls Vertex AI to generate code.

## Features

- Generate Kubernetes YAML, Terraform HCL, or Dockerfile output.
- Choose AWS, GCP, or Azure as the target cloud context.
- Backend request validation with whitelisted `type` and `cloud` values.
- Configurable GCP project, region, Vertex model, CORS origins, and prompt length via environment variables.
- `/health` endpoint for Cloud Run, Kubernetes, or load-balancer probes.
- Backend tests with FastAPI `TestClient` and mocked generation.
- Local Docker Compose setup.

## Project structure

```text
backend/   FastAPI API and Vertex AI integration
frontend/  Next.js UI with Monaco Editor preview
docker-compose.yml
.env.example
```

## Configuration

Copy the example environment file before local development:

```bash
cp .env.example .env
```

| Variable | Used by | Default | Description |
| --- | --- | --- | --- |
| `GCP_PROJECT` | Backend | `ai-infrastructure-assistant` | Google Cloud project used by Vertex AI. |
| `GCP_LOCATION` | Backend | `europe-central2` | Vertex AI region. |
| `VERTEX_MODEL` | Backend | `gemini-2.5-flash` | Generative model name. |
| `CORS_ORIGINS` | Backend | `http://localhost:3000,https://ai-infra-frontend-41844796013.europe-central2.run.app` | Comma-separated allowed frontend origins. Use exact origins in production. |
| `MAX_PROMPT_LENGTH` | Backend | `4000` | Maximum accepted prompt length. |
| `NEXT_PUBLIC_API_URL` | Frontend | `https://ai-infra-backend-41844796013.europe-central2.run.app` in production code, `http://localhost:8080` in `.env.example` | Public backend URL inlined into the browser bundle at build time. |

> `NEXT_PUBLIC_API_URL` is a browser-visible build-time value. The production fallback points to `https://ai-infra-backend-41844796013.europe-central2.run.app` so a deployed frontend does not call `localhost`. For local development, set it to `http://localhost:8080`.

## Run locally without Docker

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

The API is available at `http://localhost:8080`.

### Frontend

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8080 npm run dev
```

The app is available at `http://localhost:3000`.

## Run locally with Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

Open `http://localhost:3000` and ensure your Google Cloud credentials are available to the backend runtime if you want to call Vertex AI.

## API

### `GET /health`

Returns basic service metadata:

```json
{
  "status": "ok",
  "model": "gemini-2.5-flash",
  "location": "europe-central2"
}
```

### `POST /generate`

Request body:

```json
{
  "prompt": "Create a production-ready nginx deployment",
  "type": "kubernetes",
  "cloud": "gcp"
}
```

Allowed `type` values: `kubernetes`, `terraform`, `dockerfile`.
Allowed `cloud` values: `aws`, `gcp`, `azure`.

Response body:

```json
{
  "result": "apiVersion: apps/v1\n..."
}
```

Validation errors return HTTP `422`. Model or backend failures return proper non-2xx HTTP errors instead of embedding error text in the `result` field.

## Testing and checks

Backend:

```bash
cd backend
pytest
python -m py_compile app/*.py tests/*.py
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

## Production notes

- The GitHub Actions frontend deployment sets `NEXT_PUBLIC_API_URL` during the Cloud Run source build, because Next.js inlines `NEXT_PUBLIC_` values into the browser bundle.
- The GitHub Actions backend deployment sets `CORS_ORIGINS` to `https://ai-infra-frontend-41844796013.europe-central2.run.app` so the deployed frontend can call the API.
- Set exact `CORS_ORIGINS`; avoid `*` for authenticated deployments.
- Validate generated infrastructure code with your normal tools before deployment, for example `kubectl --dry-run`, `terraform fmt`, `terraform validate`, and Dockerfile linters.
- Do not hardcode secrets in prompts or generated code.
- Ensure Vertex AI credentials are provided through workload identity, service account credentials, or the platform-native identity mechanism.
