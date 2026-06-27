"use client";

import type { UserAnswer } from "../lib/types";

interface Props {
  answer: UserAnswer | undefined;
  weighted: boolean;
  onAnswer: (answer: UserAnswer) => void;
  onToggleWeighted: () => void;
}

export default function AnswerButtons({
  answer,
  weighted,
  onAnswer,
  onToggleWeighted,
}: Props) {
  return (
    <div className="mt-6 flex flex-col gap-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:gap-3">
        <button
          type="button"
          onClick={() => onAnswer(1)}
          className={`flex-1 rounded-xl px-4 py-3 font-semibold text-white transition ${
            answer === 1
              ? "bg-wk-green ring-2 ring-wk-green ring-offset-2"
              : "bg-wk-green/80 hover:bg-wk-green"
          }`}
        >
          ✓ Zustimmen
        </button>
        <button
          type="button"
          onClick={() => onAnswer(-1)}
          className={`flex-1 rounded-xl px-4 py-3 font-semibold text-white transition ${
            answer === -1
              ? "bg-wk-red ring-2 ring-wk-red ring-offset-2"
              : "bg-wk-red/80 hover:bg-wk-red"
          }`}
        >
          ✕ Ablehnen
        </button>
        <button
          type="button"
          onClick={() => onAnswer(0)}
          className={`flex-1 rounded-xl px-4 py-3 font-semibold text-white transition ${
            answer === 0
              ? "bg-wk-gray ring-2 ring-wk-gray ring-offset-2"
              : "bg-wk-gray/80 hover:bg-wk-gray"
          }`}
        >
          → Überspringen
        </button>
      </div>

      <label className="flex cursor-pointer items-center gap-2 text-sm text-gray-600">
        <input
          type="checkbox"
          checked={weighted}
          onChange={onToggleWeighted}
          className="h-4 w-4 rounded border-gray-300 text-wk-green focus:ring-wk-green"
        />
        <span>Doppelte Gewichtung für diese These</span>
      </label>
    </div>
  );
}
