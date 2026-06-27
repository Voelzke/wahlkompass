/**
 * Lightweight matching-flow store (no external deps).
 *
 * Uses the module singleton + useSyncExternalStore pattern. Answers are
 * persisted to localStorage keyed by electionId so the results page can
 * read them after a route change.
 */

import { useSyncExternalStore } from "react";
import type { AnswerRecord, UserAnswer } from "../lib/types";

export interface MatchingState {
  electionId: string | null;
  answers: Record<string, AnswerRecord>;
  currentIndex: number;
  tier: number; // number of theses selected
  started: boolean;
}

const STORAGE_PREFIX = "wk_answers_";

let state: MatchingState = {
  electionId: null,
  answers: {},
  currentIndex: 0,
  tier: 20,
  started: false,
};

const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((l) => l());
}

function persist(electionId: string, answers: Record<string, AnswerRecord>) {
  try {
    if (typeof localStorage !== "undefined") {
      localStorage.setItem(
        `${STORAGE_PREFIX}${electionId}`,
        JSON.stringify(answers),
      );
    }
  } catch {
    // localStorage may be unavailable (SSR / privacy mode)
  }
}

function setState(updater: (s: MatchingState) => MatchingState) {
  const next = updater(state);
  state = next;
  if (next.electionId) persist(next.electionId, next.answers);
  emit();
}

// --- Actions ---------------------------------------------------------------

export const matchingStore = {
  getState: () => state,
  subscribe(listener: () => void) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },

  start(electionId: string, tier: number) {
    const existing = loadAnswers(electionId);
    setState(() => ({
      electionId,
      answers: existing,
      currentIndex: 0,
      tier,
      started: true,
    }));
  },

  setAnswer(thesisId: string, answer: UserAnswer, weighted: boolean) {
    setState((s) => ({
      ...s,
      answers: { ...s.answers, [thesisId]: { answer, weighted } },
    }));
  },

  toggleWeighted(thesisId: string) {
    setState((s) => {
      const current = s.answers[thesisId] ?? { answer: 0 as UserAnswer, weighted: false };
      return {
        ...s,
        answers: {
          ...s.answers,
          [thesisId]: { ...current, weighted: !current.weighted },
        },
      };
    });
  },

  next() {
    setState((s) => ({ ...s, currentIndex: s.currentIndex + 1 }));
  },

  prev() {
    setState((s) => ({ ...s, currentIndex: Math.max(0, s.currentIndex - 1) }));
  },

  goTo(index: number) {
    setState((s) => ({ ...s, currentIndex: Math.max(0, index) }));
  },

  reset(electionId: string) {
    try {
      if (typeof localStorage !== "undefined") {
        localStorage.removeItem(`${STORAGE_PREFIX}${electionId}`);
      }
    } catch {
      // ignore
    }
    setState((s) => ({
      ...s,
      electionId,
      answers: {},
      currentIndex: 0,
      started: false,
    }));
  },
};

function loadAnswers(electionId: string): Record<string, AnswerRecord> {
  try {
    if (typeof localStorage !== "undefined") {
      const raw = localStorage.getItem(`${STORAGE_PREFIX}${electionId}`);
      if (raw) return JSON.parse(raw) as Record<string, AnswerRecord>;
    }
  } catch {
    // ignore
  }
  return {};
}

export function loadAnswersForElection(
  electionId: string,
): Record<string, AnswerRecord> {
  return loadAnswers(electionId);
}

// --- React hook ------------------------------------------------------------

export function useMatchingStore<T>(selector: (s: MatchingState) => T): T {
  return useSyncExternalStore(
    matchingStore.subscribe,
    () => selector(matchingStore.getState()),
    () => selector(state),
  );
}
