"use client";

import { useMemo } from "react";
import Link from "next/link";
import type { Election, Party, Position, Thesis } from "@/lib/types";
import { computeResults } from "@/lib/matching";
import { loadAnswersForElection } from "@/store/matching";
import PartyRanking from "@/components/PartyRanking";

interface Props {
  electionId: string;
  election: Election;
  parties: Party[];
  theses: Thesis[];
  positions: Position[];
}

export default function ResultsClient({
  electionId,
  election,
  parties,
  theses,
  positions,
}: Props) {
  const result = useMemo(() => {
    const answers = loadAnswersForElection(electionId);
    return computeResults(parties, theses, positions, answers);
  }, [electionId, parties, theses, positions]);

  if (!result) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <h1 className="mb-4 text-2xl font-bold text-gray-900">
          Zu wenige Antworten
        </h1>
        <p className="mb-6 text-gray-600">
          Bitte beantworten Sie mindestens 5 Thesen, um ein Ergebnis zu sehen.
        </p>
        <Link
          href={`/wahl/${electionId}`}
          className="inline-block rounded-xl bg-wk-green px-6 py-3 font-semibold text-white hover:bg-wk-green/90"
        >
          Zurück zum Fragebogen
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="mb-1 text-3xl font-bold text-gray-900">Dein Ergebnis</h1>
      <p className="mb-6 text-gray-600">
        Du hast {result.answeredCount} Thesen beantwortet.
      </p>

      <PartyRanking
        ranked={result.ranked}
        isPreview={election.is_preview || election.phase === "erfassung"}
      />

      <div className="mt-8 rounded-lg bg-blue-50 px-4 py-3 text-sm text-blue-800 ring-1 ring-blue-200">
        <p className="font-medium">KI-Transparenzhinweis</p>
        <p className="mt-1">
          Parteipositionen werden teilautomatisiert (KI-gestützt) aus
          Wahlprogrammen extrahiert und vor Veröffentlichung geprüft.
          Vergleichen Sie wichtige Aussagen mit den Originalquellen.
        </p>
      </div>

      <div className="mt-6 text-center">
        <Link
          href={`/wahl/${electionId}`}
          className="text-sm text-gray-600 hover:text-gray-900"
        >
          ← Fragebogen erneut durchlaufen
        </Link>
      </div>
    </div>
  );
}
