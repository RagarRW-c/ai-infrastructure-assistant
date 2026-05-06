"use client";

import { useState } from "react";
import Editor from "@monaco-editor/react";

export default function Home() {

  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);

  const [type, setType] = useState("kubernetes");

  async function generate() {

    setLoading(true);

    try {

      const response = await fetch(
        "https://ai-infra-backend-41844796013.europe-central2.run.app/generate",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            prompt,
            type,
          }),
        }
      );

      const data = await response.json();

      setResult(data.result);

    } catch (error) {

      console.error(error);

    } finally {

      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-black text-white p-10">

      <h1 className="text-4xl font-bold mb-8">
        AI Infrastructure Assistant
      </h1>

      <div className="flex gap-4 mb-4">

        <button
          onClick={() => setType("kubernetes")}
          className={`px-4 py-2 rounded ${
            type === "kubernetes"
              ? "bg-blue-600"
              : "bg-gray-700"
          }`}
        >
          Kubernetes
        </button>

        <button
          onClick={() => setType("terraform")}
          className={`px-4 py-2 rounded ${
            type === "terraform"
              ? "bg-blue-600"
              : "bg-gray-700"
          }`}
        >
          Terraform
        </button>

        <button
          onClick={() => setType("dockerfile")}
          className={`px-4 py-2 rounded ${
            type === "dockerfile"
              ? "bg-blue-600"
              : "bg-gray-700"
          }`}
        >
          Dockerfile
        </button>

      </div>

      <textarea
        className="w-full h-40 p-4 rounded bg-white text-black border border-gray-400"
        placeholder="Create kubernetes deployment for nginx"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
      />

      <button
        onClick={generate}
        className="mt-4 px-6 py-3 bg-blue-600 rounded"
      >
        {loading ? "Generating..." : "Generate"}
      </button>

      <div className="mt-8 border border-gray-800 rounded overflow-hidden">

        <div className="p-2 flex gap-2">

          <button
            onClick={() => navigator.clipboard.writeText(result)}
            className="px-4 py-2 bg-green-600 rounded"
          >
            Copy YAML
          </button>

          <button
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
            className="px-4 py-2 bg-purple-600 rounded"
          >
            Download
          </button>

        </div>

        <Editor
          height="600px"
          defaultLanguage="yaml"
          theme="vs-dark"
          value={result}
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

    </main>
  );
}