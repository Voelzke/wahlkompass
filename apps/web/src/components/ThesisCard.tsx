"use client";

import type { Thesis, Category } from "../lib/types";

interface Props {
  thesis: Thesis;
  category?: Category;
}

export default function ThesisCard({ thesis, category }: Props) {
  return (
    <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-gray-200 sm:p-8">
      {category && (
        <span className="mb-3 inline-block rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600">
          {category.name}
        </span>
      )}
      <h2 className="mb-2 text-xl font-bold text-gray-900 sm:text-2xl">
        {thesis.title}
      </h2>
      <p className="text-base leading-relaxed text-gray-700">{thesis.text}</p>
    </div>
  );
}
