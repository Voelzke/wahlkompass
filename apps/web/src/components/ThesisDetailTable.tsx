"use client";

import { useState } from "react";
import type { AnswerRecord, Party, Position, Thesis } from "@/lib/types";

interface Props {
  theses: Thesis[];
  parties: Party[];
  positions: Position[];
  answers: Record<string, AnswerRecord>;
}

function posColor(pos: number): string {
  if (pos === 1) return "bg-green-100 text-green-800 border-green-300";
  if (pos === -1) return "bg-red-100 text-red-800 border-red-300";
  return "bg-gray-100 text-gray-500 border-gray-200";
}

function posLabel(pos: number | undefined): string {
  if (pos === 1) return "✓";
  if (pos === -1) return "✕";
  if (pos === 0) return "–";
  return "?";
}

function userColor(ans: number): string {
  if (ans === 1) return "bg-green-500 text-white";
  if (ans === -1) return "bg-red-500 text-white";
  return "bg-gray-300 text-gray-600";
}

function userLabel(ans: number): string {
  if (ans === 1) return "Zustimmen";
  if (ans === -1) return "Ablehnen";
  return "Übersprungen";
}

export default function ThesisDetailTable({
  theses,
  parties,
  positions,
  answers,
}: Props) {
  const [expandedThesis, setExpandedThesis] = useState<string | null>(null);

  // Only show theses the user answered
  const answeredTheses = theses.filter(
    (t) => answers[t.id] && answers[t.id].answer !== 0,
  );

  // Sort parties by short_name
  const sortedParties = [...parties].sort((a, b) =>
    a.short_name.localeCompare(b.short_name, "de"),
  );

  return (
    <div>
      <h2 className="mb-1 text-xl font-bold text-gray-900">
        Detail-Analyse: These für These
      </h2>
      <p className="mb-4 text-sm text-gray-600">
        Klicke auf eine These, um die Zitate aus den Wahlprogrammen der
        Parteien zu sehen. Grün = Zustimmung, Rot = Ablehnung, Grau = Neutral.
      </p>

      {/* Legend */}
      <div className="mb-4 flex flex-wrap gap-3 text-xs">
        <span className="flex items-center gap-1">
          <span className="inline-block h-4 w-4 rounded bg-green-100 border border-green-300" />
          Zustimmen
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-4 w-4 rounded bg-red-100 border border-red-300" />
          Ablehnen
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-4 w-4 rounded bg-gray-100 border border-gray-200" />
          Neutral / Unklar
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-4 w-4 rounded bg-green-500" />
          Deine Antwort: Zustimmen
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-4 w-4 rounded bg-red-500" />
          Deine Antwort: Ablehnen
        </span>
      </div>

      {/* Thesis list */}
      <div className="space-y-2">
        {answeredTheses.map((thesis) => {
          const userAns = answers[thesis.id];
          const isExpanded = expandedThesis === thesis.id;

          return (
            <div
              key={thesis.id}
              className="rounded-xl bg-white shadow-sm ring-1 ring-gray-200"
            >
              {/* Thesis header row */}
              <button
                type="button"
                onClick={() =>
                  setExpandedThesis(isExpanded ? null : thesis.id)
                }
                className="flex w-full items-center justify-between gap-3 p-4 text-left"
              >
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{thesis.text}</p>
                  <p className="mt-1 text-xs text-gray-400">
                    Klick zum {isExpanded ? "Ausblenden" : "Erweitern"}
                  </p>
                </div>
                <span
                  className={`flex h-8 items-center rounded-lg px-3 text-xs font-medium ${userColor(
                    userAns.answer,
                  )}`}
                >
                  Du: {userLabel(userAns.answer)}
                  {userAns.weighted && " (2×)"}
                </span>
                <span className="text-gray-400">{isExpanded ? "▲" : "▼"}</span>
              </button>

              {/* Expanded: show all parties */}
              {isExpanded && (
                <div className="border-t border-gray-100 p-4">
                  <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
                    {sortedParties.map((party) => {
                      const pos = positions.find(
                        (p) =>
                          p.party_id === party.id &&
                          p.thesis_id === thesis.id,
                      );
                      const partyPos = pos?.position;
                      const quote = pos?.source_quote;
                      const source = pos?.source_url;
                      const match =
                        userAns.answer !== 0 && partyPos !== undefined
                          ? userAns.answer * partyPos
                          : null;

                      return (
                        <div
                          key={party.id}
                          className={`rounded-lg border p-3 ${posColor(
                            partyPos ?? 0,
                          )}`}
                        >
                          <div className="mb-1 flex items-center gap-2">
                            <span
                              className="h-3 w-3 rounded-full"
                              style={{ backgroundColor: party.color }}
                            />
                            <span className="font-medium">
                              {party.short_name}
                            </span>
                            {match !== null && (
                              <span className="ml-auto text-xs">
                                {match > 0
                                  ? "✓ Übereinstimmung"
                                  : match < 0
                                    ? "✕ Gegenposition"
                                    : "– Neutral"}
                              </span>
                            )}
                          </div>
                          <p className="text-xs">
                            Position:{" "}
                            {partyPos === 1
                              ? "Zustimmen"
                              : partyPos === -1
                                ? "Ablehnen"
                                : partyPos === 0
                                  ? "Neutral"
                                  : "Keine Daten"}
                          </p>
                          {quote && (
                            <p className="mt-2 border-l-2 border-gray-300 pl-2 text-xs italic text-gray-700">
                              „{quote}"
                            </p>
                          )}
                          {source && (
                            <p className="mt-1 text-xs text-gray-400">
                              {source}
                            </p>
                          )}
                          {!quote && (
                            <p className="mt-2 text-xs text-gray-400">
                              Kein Beleg verfügbar
                            </p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {answeredTheses.length === 0 && (
        <p className="text-center text-gray-500">
          Keine Thesen beantwortet.
        </p>
      )}
    </div>
  );
}
