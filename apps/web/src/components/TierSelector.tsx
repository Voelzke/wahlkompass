"use client";

import type { Tier } from "../lib/types";

interface Props {
  tiers: Tier[];
  selected: number | null;
  onSelect: (count: number) => void;
}

export default function TierSelector({ tiers, selected, onSelect }: Props) {
  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-2 text-center text-2xl font-bold text-gray-900">
        Wie viele Thesen möchtest du beantworten?
      </h1>
      <p className="mb-8 text-center text-gray-600">
        Du kannst jederzeit Thesen überspringen.
      </p>

      <div className="grid gap-4 sm:grid-cols-3">
        {tiers.map((tier) => (
          <button
            key={tier.id}
            type="button"
            onClick={() => onSelect(tier.count)}
            className={`rounded-2xl border-2 p-5 text-left transition ${
              selected === tier.count
                ? "border-wk-green bg-green-50"
                : "border-gray-200 bg-white hover:border-gray-300"
            }`}
          >
            <div className="mb-1 text-lg font-bold text-gray-900">
              {tier.label}
            </div>
            <div className="text-sm text-gray-500">{tier.count} Thesen</div>
            <div className="mt-2 text-xs text-gray-400">{tier.id}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

export function defaultTiers(): Tier[] {
  return [
    { id: "kurz", label: "Kurz", count: 20 },
    { id: "mittel", label: "Mittel", count: 40 },
    { id: "lang", label: "Lang", count: 60 },
  ];
}
