"use client";

import { useState } from "react";
import Editor from "@monaco-editor/react";

export default function Home() {

  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);

  const [type, setType] = useState("kubernetes");

  const [cloud, setCloud] = useState("gcp");

  console.log("ENV:", process.env.NEXT_PUBLIC_API_URL)

  async function generate() {

    setLoading(true);

    try {

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/generate`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            prompt,
            type,
            cloud,
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

      <div className="flex gap-4 mb-6">

  <button
    onClick={() => setCloud("aws")}
    className={`px-4 py-2 rounded ${
      cloud === "aws"
        ? "bg-orange-600"
        : "bg-gray-700"
    }`}
  >
    AWS
  </button>

  <button
    onClick={() => setCloud("gcp")}
    className={`px-4 py-2 rounded ${
      cloud === "gcp"
        ? "bg-blue-600"
        : "bg-gray-700"
    }`}
  >
    GCP
  </button>

  <button
    onClick={() => setCloud("azure")}
    className={`px-4 py-2 rounded ${
      cloud === "azure"
        ? "bg-cyan-600"
        : "bg-gray-700"
    }`}
  >
    Azure
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
          language={
            type === "terraform"
            ? "hcl"
            : type === "dockerfile"
            ? "dockerfile"
            : "yaml"
          }
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