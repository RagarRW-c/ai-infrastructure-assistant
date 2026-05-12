"use client";

import { useMemo, useState } from "react";
import Editor from "@monaco-editor/react";

type InfraType = "kubernetes" | "terraform" | "dockerfile";
type CloudProvider = "aws" | "gcp" | "azure";

const DEFAULT_API_BASE_URL = "https://ai-infra-backend-41844796013.europe-central2.run.app";
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_BASE_URL;
const MAX_PROMPT_LENGTH = 4000;

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

function getErrorMessage(payload: unknown, fallback: string) {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail?: unknown }).detail;
    if (typeof detail === "string") {
      return detail;
    }
  }

  return fallback;
}

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [type, setType] = useState<InfraType>("kubernetes");
  const [cloud, setCloud] = useState<CloudProvider>("gcp");

  const selectedInfra = useMemo(
    () => infraOptions.find((option) => option.value === type) ?? infraOptions[0],
    [type]
  );

  const isPromptValid = prompt.trim().length > 0 && prompt.length <= MAX_PROMPT_LENGTH;
  const copyLabel = `Copy ${selectedInfra.label}`;

  async function generate() {
    if (!isPromptValid || loading) {
      return;
    }

    setLoading(true);
    setError("");

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
        throw new Error(getErrorMessage(data, "Generation failed."));
      }

      if (!data || typeof data !== "object" || !("result" in data)) {
        throw new Error("Backend returned an unexpected response.");
      }

      setResult(String((data as { result: unknown }).result));
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
          />
          <div className="mt-2 flex flex-wrap items-center justify-between gap-3 text-sm text-gray-400">
            <span>{prompt.length}/{MAX_PROMPT_LENGTH} characters</span>
            <span>Backend: {API_BASE_URL}</span>
          </div>

          {error ? (
            <div className="mt-4 rounded border border-red-500 bg-red-950 px-4 py-3 text-red-100">
              {error}
            </div>
          ) : null}

          <button
            type="button"
            onClick={generate}
            disabled={!isPromptValid || loading}
            className="mt-4 rounded bg-blue-600 px-6 py-3 font-semibold transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-gray-600"
          >
            {loading ? "Generating..." : "Generate"}
          </button>
        </div>

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
                onClick={() => navigator.clipboard.writeText(result)}
                disabled={!result}
                className="rounded bg-green-600 px-4 py-2 transition hover:bg-green-500 disabled:cursor-not-allowed disabled:bg-gray-600"
              >
                {copyLabel}
              </button>

              <button
                type="button"
                onClick={() => {
                  const blob = new Blob([result], {
                    type: "text/plain",
                  });
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = `${type}.txt`;
                  a.click();
                  window.URL.revokeObjectURL(url);
                }}
                disabled={!result}
                className="rounded bg-purple-600 px-4 py-2 transition hover:bg-purple-500 disabled:cursor-not-allowed disabled:bg-gray-600"
              >
                Download
              </button>
            </div>
          </div>

          <Editor
            height="600px"
            language={selectedInfra.language}
            theme="vs-dark"
            value={result || "// Generated code will appear here"}
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
