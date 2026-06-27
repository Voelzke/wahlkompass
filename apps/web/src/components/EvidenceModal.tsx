"use client";

import type { RankedParty } from "../lib/matching";

interface Props {
  party: RankedParty;
  onClose: () => void;
}

export default function EvidenceModal({ party, onClose }: Props) {
  const withEvidence = party.perThesis.filter(
    (m) => m.position && (m.position.source_quote || m.position.source_url),
  );

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
    >
      <div
        className="max-h-[80vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-bold">
            Belege — {party.party.name}
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-2 py-1 text-gray-400 hover:bg-gray-100 hover:text-gray-700"
          >
            ✕
          </button>
        </div>

        {withEvidence.length === 0 ? (
          <p className="text-sm text-gray-500">
            Für diese Partei sind aktuell keine Belege hinterlegt.
          </p>
        ) : (
          <ul className="space-y-4">
            {withEvidence.map((m) => (
              <li key={m.thesis.id} className="border-b border-gray-100 pb-3">
                <p className="mb-1 font-medium text-gray-900">
                  {m.thesis.title}
                </p>
                {m.position!.source_quote && (
                  <blockquote className="border-l-2 border-gray-200 pl-3 text-sm italic text-gray-600">
                    „{m.position!.source_quote}"
                  </blockquote>
                )}
                {m.position!.source_url && (
                  <a
                    href={m.position!.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-1 inline-block text-sm text-blue-600 hover:underline"
                  >
                    Quelle öffnen →
                  </a>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
