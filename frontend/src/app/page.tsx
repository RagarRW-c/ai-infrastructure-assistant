"use client";

import { useMemo, useState } from "react";
import Editor from "@monaco-editor/react";

type InfraType = "kubernetes" | "terraform" | "dockerfile";
type CloudProvider = "aws" | "gcp" | "azure";
type ValidationStatus = "passed" | "warning" | "failed";

type ValidationResult = {
  status: ValidationStatus;
  messages: string[];
};

type ExamplePrompt = {
  title: string;
  description: string;
  prompt: string;
  type: InfraType;
  cloud: CloudProvider;
};

const DEFAULT_API_BASE_URL = "https://ai-infra-backend-41844796013.europe-central2.run.app";
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_BASE_URL;
const MAX_PROMPT_LENGTH = 4000;
const SHOW_BACKEND_INFO = process.env.NODE_ENV === "development";

const infraOptions: Array<{ value: InfraType; label: string; language: string }> = [
  { value: "kubernetes", label: "Kubernetes", language: "yaml" },
  { value: "terraform", label: "Terraform", language: "hcl" },
  { value: "dockerfile", label: "Dockerfile", language: "dockerfile" },
];

const cloudOptions: Array<{ value: CloudProvider; label: string; activeClass: string }> = [
  { value: "aws", label: "AWS", activeClass: "bg-orange-600" },
  { value: "gcp", label: "GCP", activeClass: "bg-blue-600" },
  { value: "azure", label: "Azure", activeClass: "bg-cyan-600" },
];

const placeholders: Record<InfraType, string> = {
  kubernetes: "Create a production-ready Kubernetes deployment and service for nginx",
  terraform: "Create Terraform for a secure GCP Cloud Run service",
  dockerfile: "Create a secure multi-stage Dockerfile for a Next.js application",
};

const downloadFileNames: Record<InfraType, string> = {
  kubernetes: "kubernetes.yaml",
  terraform: "main.tf",
  dockerfile: "Dockerfile",
};

const emptyEditorText = `# Your generated infrastructure code will appear here.
# Pick an example or describe what you need, then press Ctrl+Enter or Cmd+Enter to generate.`;

const examplePrompts: ExamplePrompt[] = [
  {
    title: "AWS VPC",
    description: "Terraform network baseline",
    type: "terraform",
    cloud: "aws",
    prompt:
      "Create a production-ready AWS VPC with public and private subnets across two availability zones, NAT gateway, route tables, and least-privilege security groups.",
  },
  {
    title: "GKE workload",
    description: "Kubernetes app manifests",
    type: "kubernetes",
    cloud: "gcp",
    prompt:
      "Create Kubernetes manifests for a Node.js web application on GKE with Deployment, Service, resource requests and limits, readiness and liveness probes, and secure defaults.",
  },
  {
    title: "FastAPI image",
    description: "Secure Dockerfile",
    type: "dockerfile",
    cloud: "aws",
    prompt:
      "Create a secure production Dockerfile for a Python FastAPI application using a slim base image, dependency caching, non-root user, and uvicorn startup command.",
  },
  {
    title: "Cloud Run service",
    description: "Terraform deployment",
    type: "terraform",
    cloud: "gcp",
    prompt:
      "Create Terraform for a Google Cloud Run service with Artifact Registry, service account, least-privilege IAM, environment variables, and secure production defaults.",
  },
];

const validationStyles: Record<ValidationStatus, { label: string; className: string }> = {
  passed: {
    label: "Validation passed",
    className: "border-green-600 bg-green-950 text-green-100",
  },
  warning: {
    label: "Validation warnings",
    className: "border-yellow-500 bg-yellow-950 text-yellow-100",
  },
  failed: {
    label: "Validation failed",
    className: "border-red-500 bg-red-950 text-red-100",
  },
};

function getErrorMessage(payload: unknown, fallback: string) {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail?: unknown }).detail;
    if (typeof detail === "string") {
      return detail;
    }
  }

  return fallback;
}

function isValidationResult(value: unknown): value is ValidationResult {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as { status?: unknown; messages?: unknown };
  return (
    (candidate.status === "passed" ||
      candidate.status === "warning" ||
      candidate.status === "failed") &&
    Array.isArray(candidate.messages) &&
    candidate.messages.every((message) => typeof message === "string")
  );
}

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState("");
  const [error, setError] = useState("");
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);
  const [type, setType] = useState<InfraType>("kubernetes");
  const [cloud, setCloud] = useState<CloudProvider>("gcp");

  const selectedInfra = useMemo(
    () => infraOptions.find((option) => option.value === type) ?? infraOptions[0],
    [type]
  );

  const isPromptValid = prompt.trim().length > 0 && prompt.length <= MAX_PROMPT_LENGTH;
  const copyLabel = copied ? "Copied!" : `Copy ${selectedInfra.label}`;
  const downloadFileName = downloadFileNames[type];

  function applyExample(example: ExamplePrompt) {
    setType(example.type);
    setCloud(example.cloud);
    setPrompt(example.prompt);
    setError("");
    setValidation(null);
    setCopied(false);
  }

  async function copyResult() {
    if (!result) {
      return;
    }

    try {
      await navigator.clipboard.writeText(result);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("Could not copy the generated code to clipboard.");
    }
  }

  function downloadResult() {
    if (!result) {
      return;
    }

    const blob = new Blob([result], {
      type: "text/plain",
    });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = downloadFileName;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  async function generate() {
    if (!isPromptValid || loading) {
      return;
    }

    setLoading(true);
    setError("");
    setValidation(null);
    setCopied(false);

    try {
      const response = await fetch(`${API_BASE_URL}/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt: prompt.trim(),
          type,
          cloud,
        }),
      });

      const data: unknown = await response.json();

      if (!response.ok) {
        const fallbackMessage =
          response.status === 429
            ? "Too many requests. Please wait a moment and try again."
            : "Generation failed.";
        throw new Error(getErrorMessage(data, fallbackMessage));
      }

      if (!data || typeof data !== "object" || !("result" in data)) {
        throw new Error("Backend returned an unexpected response.");
      }

      const payload = data as { result: unknown; validation?: unknown };
      setResult(String(payload.result));

      if (isValidationResult(payload.validation)) {
        setValidation(payload.validation);
      }
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : "Generation failed.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-black p-6 text-white sm:p-10">
      <section className="mx-auto flex max-w-6xl flex-col gap-8">
        <div>
          <p className="mb-2 text-sm font-semibold uppercase tracking-[0.25em] text-blue-300">
            DevOps code generator
          </p>
          <h1 className="text-4xl font-bold">AI Infrastructure Assistant</h1>
          <p className="mt-3 max-w-2xl text-gray-300">
            Generate infrastructure snippets for Kubernetes, Terraform, or Dockerfile workflows.
            Always review and validate generated code before using it in production.
          </p>
        </div>

        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
          {examplePrompts.map((example) => (
            <button
              key={example.title}
              type="button"
              onClick={() => applyExample(example)}
              className="rounded-2xl border border-gray-800 bg-gray-950 p-4 text-left transition hover:border-blue-500 hover:bg-gray-900"
            >
              <div className="text-sm font-semibold text-blue-300">{example.title}</div>
              <div className="mt-1 text-sm text-gray-300">{example.description}</div>
              <div className="mt-3 text-xs uppercase tracking-wide text-gray-500">
                {example.cloud} · {example.type}
              </div>
            </button>
          ))}
        </div>

        <div className="rounded-2xl border border-gray-800 bg-gray-950 p-5 shadow-2xl">
          <div className="mb-5 grid gap-4 md:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-300">Output type</label>
              <div className="flex flex-wrap gap-3">
                {infraOptions.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setType(option.value)}
                    className={`rounded px-4 py-2 transition hover:bg-blue-500 ${
                      type === option.value ? "bg-blue-600" : "bg-gray-700"
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-300">Cloud provider</label>
              <div className="flex flex-wrap gap-3">
                {cloudOptions.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setCloud(option.value)}
                    className={`rounded px-4 py-2 transition hover:bg-gray-600 ${
                      cloud === option.value ? option.activeClass : "bg-gray-700"
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <label className="mb-2 block text-sm font-medium text-gray-300" htmlFor="prompt">
            Prompt
          </label>
          <textarea
            id="prompt"
            className="h-40 w-full rounded border border-gray-400 bg-white p-4 text-black"
            maxLength={MAX_PROMPT_LENGTH}
            placeholder={placeholders[type]}
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            onKeyDown={(event) => {
              if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
                event.preventDefault();
                void generate();
              }
            }}
          />
          <div className="mt-2 flex flex-wrap items-center justify-between gap-3 text-sm text-gray-400">
            <span>{prompt.length}/{MAX_PROMPT_LENGTH} characters</span>
            {SHOW_BACKEND_INFO ? <span>Backend: {API_BASE_URL}</span> : null}
          </div>

          {error ? (
            <div className="mt-4 rounded border border-red-500 bg-red-950 px-4 py-3 text-red-100">
              {error}
            </div>
          ) : null}

          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={generate}
              disabled={!isPromptValid || loading}
              className="rounded bg-blue-600 px-6 py-3 font-semibold transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-gray-600"
            >
              {loading ? "Generating..." : "Generate"}
            </button>
            <span className="text-sm text-gray-400">Shortcut: Ctrl+Enter or Cmd+Enter</span>
          </div>
        </div>

        {validation ? (
          <div className={`rounded-2xl border p-4 ${validationStyles[validation.status].className}`}>
            <h2 className="font-semibold">{validationStyles[validation.status].label}</h2>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
              {validation.messages.map((message, index) => (
                <li key={`${validation.status}-${index}`}>{message}</li>
              ))}
            </ul>
          </div>
        ) : null}

        <div className="overflow-hidden rounded-2xl border border-gray-800 bg-gray-950">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-800 p-3">
            <div>
              <h2 className="font-semibold">Generated {selectedInfra.label}</h2>
              <p className="text-sm text-gray-400">
                Preview only. Run your normal validators before deployment.
              </p>
            </div>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={copyResult}
                disabled={!result}
                className="rounded bg-green-600 px-4 py-2 transition hover:bg-green-500 disabled:cursor-not-allowed disabled:bg-gray-600"
              >
                {copyLabel}
              </button>

              <button
                type="button"
                onClick={downloadResult}
                disabled={!result}
                className="rounded bg-purple-600 px-4 py-2 transition hover:bg-purple-500 disabled:cursor-not-allowed disabled:bg-gray-600"
              >
                Download {downloadFileName}
              </button>
            </div>
          </div>

          <Editor
            height="600px"
            language={selectedInfra.language}
            theme="vs-dark"
            value={result || emptyEditorText}
            options={{
              minimap: {
                enabled: false,
              },
              fontSize: 14,
              wordWrap: "on",
              readOnly: true,
              scrollBeyondLastLine: false,
            }}
          />
        </div>
      </section>
    </main>
  );
}
