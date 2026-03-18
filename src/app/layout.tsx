import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AppealAI | AI-Powered Insurance Appeal Letters",
  description: "Fight insurance claim denials with AI-generated, medically-cited appeal letters. Powered by Claude with RAG over medical necessity guidelines and live PubMed evidence.",
  keywords: "prior authorization, appeal letter, insurance denial, medical necessity, healthcare AI, AppealAI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}
