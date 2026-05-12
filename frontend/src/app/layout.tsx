import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Infrastructure Assistant",
  description: "Generate Kubernetes, Terraform, and Dockerfile snippets with AI.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
