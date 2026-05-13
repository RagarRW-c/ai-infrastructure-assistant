# AI Infrastructure Assistant Frontend

Next.js UI for AI Infrastructure Assistant. The app sends prompts to the FastAPI backend and previews generated Kubernetes, Terraform, or Dockerfile code in Monaco Editor.

## Environment

Set the backend URL before running or building locally:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8080
```

`NEXT_PUBLIC_API_URL` is visible to the browser and is inlined at build time. If it is not set, the app falls back to the deployed backend at `https://ai-infra-backend-41844796013.europe-central2.run.app`.

## Development

```bash
npm install
NEXT_PUBLIC_API_URL=http://localhost:8080 npm run dev
```

Open `http://localhost:3000`.

## Checks

```bash
npm run lint
npm run build
```
