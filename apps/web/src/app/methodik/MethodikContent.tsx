"use client";

import { useMemo } from "react";

interface Props {
  markdown: string;
}

/** Minimal markdown renderer (headings, paragraphs, lists, blockquotes, bold). */
export default function MethodikContent({ markdown }: Props) {
  const html = useMemo(() => renderMarkdown(markdown), [markdown]);

  return (
    <div>
      <h1 className="mb-6 text-3xl font-bold text-gray-900">Methodik</h1>
      <article
        className="prose prose-sm max-w-none text-gray-700 [&_blockquote]:rounded [&_blockquote]:border-l-4 [&_blockquote]:border-amber-300 [&_blockquote]:bg-amber-50 [&_blockquote]:px-4 [&_blockquote]:py-2 [&_h1]:text-2xl [&_h1]:font-bold [&_h1]:text-gray-900 [&_h2]:mt-6 [&_h2]:text-xl [&_h2]:font-semibold [&_h2]:text-gray-900 [&_li]:ml-4 [&_li]:list-disc"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </div>
  );
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function inline(s: string): string {
  let out = escapeHtml(s);
  // bold
  out = out.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  // inline code
  out = out.replace(/`(.+?)`/g, "<code>$1</code>");
  return out;
}

function renderMarkdown(md: string): string {
  const lines = md.split("\n");
  const html: string[] = [];
  let inList = false;
  let inQuote = false;

  for (const raw of lines) {
    const line = raw.trimEnd();

    // blockquote
    if (line.startsWith("> ")) {
      if (!inQuote) html.push("<blockquote>");
      inQuote = true;
      html.push(`<p>${inline(line.slice(2))}</p>`);
      continue;
    }
    if (inQuote) {
      html.push("</blockquote>");
      inQuote = false;
    }

    // headings
    if (line.startsWith("### ")) {
      if (inList) { html.push("</ul>"); inList = false; }
      html.push(`<h3>${inline(line.slice(4))}</h3>`);
      continue;
    }
    if (line.startsWith("## ")) {
      if (inList) { html.push("</ul>"); inList = false; }
      html.push(`<h2>${inline(line.slice(3))}</h2>`);
      continue;
    }
    if (line.startsWith("# ")) {
      if (inList) { html.push("</ul>"); inList = false; }
      html.push(`<h1>${inline(line.slice(2))}</h1>`);
      continue;
    }

    // list items
    if (line.startsWith("- ") || line.startsWith("* ")) {
      if (!inList) { html.push("<ul>"); inList = true; }
      html.push(`<li>${inline(line.slice(2))}</li>`);
      continue;
    }

    // close list on blank or non-list line
    if (inList && line.trim() === "") {
      html.push("</ul>");
      inList = false;
    }

    if (line.trim() === "") {
      continue;
    }

    html.push(`<p>${inline(line)}</p>`);
  }

  if (inList) html.push("</ul>");
  if (inQuote) html.push("</blockquote>");

  return html.join("\n");
}
