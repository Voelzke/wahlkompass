"use client";

import { useState } from "react";
import type { RankedParty } from "../lib/matching";
import EvidenceModal from "./EvidenceModal";

interface Props {
  ranked: RankedParty[];
  isPreview?: boolean;
}

export default function PartyRanking({ ranked, isPreview }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const [evidenceFor, setEvidenceFor] = useState<RankedParty | null>(null);

  return (
    <div>
      {isPreview && (
        <div className="mb-4 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800 ring-1 ring-amber-200">
          ⚠️ Hinweis: Noch nicht alle Parteipositionen sind erfasst. Ergebnisse
          können sich noch ändern.
        </div>
      )}

      <ol className="space-y-3">
        {ranked.map((rp) => (
          <li
            key={rp.party.id}
            className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-200"
          >
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-100 text-sm font-bold text-gray-700">
                  {rp.rank}
                </span>
                <span
                  className="h-4 w-4 rounded-full"
                  style={{ backgroundColor: rp.party.color }}
                />
                <span className="font-semibold text-gray-900">
                  {rp.party.short_name}
                </span>
              </div>
              <span className="text-lg font-bold text-wk-green">
                {rp.percentage}% Übereinstimmung
              </span>
            </div>

            <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-gray-100">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${rp.percentage}%`,
                  backgroundColor: rp.party.color,
                }}
              />
            </div>

            <div className="mt-3 flex gap-3">
              <button
                type="button"
                onClick={() =>
                  setExpanded(expanded === rp.party.id ? null : rp.party.id)
                }
                className="text-sm font-medium text-gray-600 hover:text-gray-900"
              >
                {expanded === rp.party.id
                  ? "Details ausblenden"
                  : "These-für-These"}
              </button>
              <button
                type="button"
                onClick={() => setEvidenceFor(rp)}
                className="text-sm font-medium text-gray-600 hover:text-gray-900"
              >
                Belege
              </button>
            </div>

            {expanded === rp.party.id && (
              <table className="mt-3 w-full border-t border-gray-100 text-sm">
                <thead>
                  <tr className="text-left text-xs text-gray-500">
                    <th className="py-2 pr-2">These</th>
                    <th className="py-2 px-2 text-center">Du</th>
                    <th className="py-2 px-2 text-center">Partei</th>
                    <th className="py-2 px-2 text-center">Match</th>
                    <th className="py-2 pl-2">Zitat aus dem Programm</th>
                  </tr>
                </thead>
                <tbody>
                  {rp.perThesis
                    .filter((m) => m.userAnswer !== 0)
                    .map((m) => {
                      const posLabel =
                        m.position?.position === 1
                          ? "Zustimmen"
                          : m.position?.position === -1
                            ? "Ablehnen"
                            : m.position?.position === 0
                              ? "Neutral"
                              : "—";
                      const userLabel =
                        m.userAnswer === 1
                          ? "Zustimmen"
                          : m.userAnswer === -1
                            ? "Ablehnen"
                            : "—";
                      return (
                        <tr key={m.thesis.id} className="border-t border-gray-50">
                          <td className="py-2 pr-2">
                            <span className="font-medium">{m.thesis.text}</span>
                            {m.weighted && (
                              <span className="ml-2 rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-500">
                                2× gewichtet
                              </span>
                            )}
                          </td>
                          <td className="py-2 px-2 text-center">
                            <span className={
                              m.userAnswer === 1
                                ? "text-wk-green font-medium"
                                : m.userAnswer === -1
                                  ? "text-wk-red font-medium"
                                  : "text-wk-gray"
                            }>
                              {userLabel}
                            </span>
                          </td>
                          <td className="py-2 px-2 text-center">
                            <span className={
                              m.position?.position === 1
                                ? "text-wk-green font-medium"
                                : m.position?.position === -1
                                  ? "text-wk-red font-medium"
                                  : "text-wk-gray"
                            }>
                              {posLabel}
                            </span>
                          </td>
                          <td className="py-2 px-2 text-center">
                            <span className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold text-white ${
                              m.match > 0
                                ? "bg-wk-green"
                                : m.match < 0
                                  ? "bg-wk-red"
                                  : "bg-wk-gray"
                            }`}>
                              {m.match > 0 ? "✓" : m.match < 0 ? "✕" : "–"}
                            </span>
                          </td>
                          <td className="py-2 pl-2 text-gray-600 text-xs">
                            {m.position?.source_quote ? (
                              <span>"{m.position.source_quote}"</span>
                            ) : (
                              <span className="text-gray-400">—</span>
                            )}
                            {m.position?.source_url && (
                              <span className="block text-gray-400">
                                {m.position.source_url}
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            )}
          </li>
        ))}
      </ol>

      {evidenceFor && (
        <EvidenceModal party={evidenceFor} onClose={() => setEvidenceFor(null)} />
      )}
    </div>
  );
}
