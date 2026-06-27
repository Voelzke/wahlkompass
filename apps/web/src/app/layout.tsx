import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Wahlkompass",
  description:
    "Vergleiche deine Positionen mit allen antretenden Parteien — Open Source.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="de">
      <body className="flex min-h-screen flex-col">
        <header className="border-b border-gray-200 bg-white">
          <nav className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3">
            <a href="/" className="text-lg font-bold text-gray-900">
              Wahl<span className="text-wk-green">kompass</span>
            </a>
            <div className="flex gap-4 text-sm">
              <a href="/" className="text-gray-600 hover:text-gray-900">
                Start
              </a>
              <a
                href="/methodik"
                className="text-gray-600 hover:text-gray-900"
              >
                Methodik
              </a>
              <a
                href="/impressum"
                className="text-gray-600 hover:text-gray-900"
              >
                Impressum
              </a>
            </div>
          </nav>
        </header>

        <main className="flex-1">{children}</main>

        <footer className="border-t border-gray-200 bg-white">
          <div className="mx-auto max-w-4xl px-4 py-6 text-sm text-gray-500">
            <p className="mb-2">
              <a
                href="https://github.com/wahlkompass/wahlkompass"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-600 hover:text-gray-900"
              >
                GitHub
              </a>{" "}
              · AGPL-3.0 (Code) · CC-BY-SA 4.0 (Daten)
            </p>
            <p className="text-xs text-gray-400">
              KI-Transparenz: Parteipositionen werden teilautomatisiert (KI)
              extrahiert und vor Veröffentlichung geprüft.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
