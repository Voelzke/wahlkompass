"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import type { Category, Thesis, UserAnswer } from "@/lib/types";
import { matchingStore, useMatchingStore } from "@/store/matching";
import ThesisCard from "@/components/ThesisCard";
import AnswerButtons from "@/components/AnswerButtons";
import ProgressBar from "@/components/ProgressBar";
import TierSelector, { defaultTiers } from "@/components/TierSelector";

interface Props {
  electionId: string;
  electionTitle: string;
  theses: Thesis[];
  categories: Category[];
}

/**
 * Returns theses filtered by tier.
 * tier "20" → all theses with tier "20" (20 theses)
 * tier "40" → all theses with tier "20" or "40" (40 theses)
 * tier "60plus" → all theses (60 theses)
 */
function filterByTier(theses: Thesis[], tierCount: number): Thesis[] {
  if (tierCount <= 20) {
    return theses.filter((t) => t.tier === "20");
  } else if (tierCount <= 40) {
    return theses.filter((t) => t.tier === "20" || t.tier === "40");
  } else {
    return theses;
  }
}

export default function MatchingFlow({
  electionId,
  electionTitle,
  theses,
  categories,
}: Props) {
  const router = useRouter();
  const [tierSelected, setTierSelected] = useState<number | null>(null);

  const started = useMatchingStore((s) => s.started && s.electionId === electionId);
  const currentIndex = useMatchingStore((s) => s.currentIndex);
  const answers = useMatchingStore((s) => s.answers);

  // Tier selector screen
  if (!started || tierSelected === null) {
    const tiers = defaultTiers().map((t) => ({
      ...t,
      count: Math.min(t.count, theses.length),
    }));

    return (
      <div className="mx-auto max-w-4xl px-4 py-12">
        <h1 className="mb-1 text-center text-2xl font-bold text-gray-900">
          {electionTitle}
        </h1>
        <TierSelector
          tiers={tiers}
          selected={tierSelected}
          onSelect={(count) => {
            setTierSelected(count);
            matchingStore.start(electionId, count);
          }}
        />
      </div>
    );
  }

  const activeTheses = useMemo(
    () => filterByTier(theses, tierSelected),
    [theses, tierSelected],
  );

  if (currentIndex >= activeTheses.length) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <h1 className="mb-4 text-2xl font-bold">Fast geschafft!</h1>
        <p className="mb-6 text-gray-600">
          Du hast alle {activeTheses.length} Thesen durchlaufen. Jetzt kannst du
          dein Ergebnis ansehen.
        </p>
        <button
          type="button"
          onClick={() => router.push(`/wahl/${electionId}/ergebnis`)}
          className="rounded-xl bg-wk-green px-6 py-3 font-semibold text-white hover:bg-wk-green/90"
        >
          Ergebnis anzeigen
        </button>
      </div>
    );
  }

  const thesis = activeTheses[currentIndex];
  const category = categories.find((c) => c.id === thesis.category_id);
  const currentAnswer = answers[thesis.id];

  function handleAnswer(answer: UserAnswer) {
    const wasWeighted = currentAnswer?.weighted ?? false;
    matchingStore.setAnswer(thesis.id, answer, wasWeighted);
    setTimeout(() => {
      matchingStore.next();
    }, 150);
  }

  function handleToggleWeighted() {
    matchingStore.toggleWeighted(thesis.id);
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <div className="mb-6">
        <ProgressBar current={currentIndex + 1} total={activeTheses.length} />
      </div>

      <ThesisCard thesis={thesis} category={category} />

      <AnswerButtons
        answer={currentAnswer?.answer}
        weighted={currentAnswer?.weighted ?? false}
        onAnswer={handleAnswer}
        onToggleWeighted={handleToggleWeighted}
      />

      <div className="mt-6 flex justify-between">
        <button
          type="button"
          onClick={() => matchingStore.prev()}
          disabled={currentIndex === 0}
          className="rounded-lg px-4 py-2 text-sm text-gray-600 disabled:opacity-30"
        >
          ← Zurück
        </button>
        <button
          type="button"
          onClick={() => matchingStore.next()}
          className="rounded-lg px-4 py-2 text-sm text-gray-600"
        >
          Überspringen →
        </button>
      </div>
    </div>
  );
}
