/**
 * Matching / scoring logic for the Wahlkompass.
 *
 * Algorithm (per task spec):
 *   match(p, t)   = s_user(t) * s_party(p, t)          s_user ∈ {+1,-1,0}, s_party ∈ {+1,-1,0}
 *   weighted(p,t) = match(p, t) * w(t)                  w(t) ∈ {1, 2}
 *   score(p)      = Σ weighted(p, t)
 *   norm(p)       = score(p) / Σ |w(t)|  for non-skipped theses only  →  [-1, +1]
 *
 * Result list sorted descending by norm; ties share a rank and are ordered
 * alphabetically by party short_name.
 *
 * Minimum 5 answered (non-skipped) theses are required, otherwise the result
 * is null and the caller must show a prompt.
 */

import type {
  AnswerRecord,
  Party,
  Position,
  Thesis,
  UserAnswer,
} from "./types";

export interface ThesisMatch {
  thesis: Thesis;
  position: Position | null;
  userAnswer: UserAnswer;
  weighted: boolean;
  /** s_user * s_party */
  match: number;
  /** match * w(t) */
  weightedMatch: number;
}

export interface PartyScore {
  party: Party;
  score: number;
  norm: number; // [-1, +1]
  percentage: number; // 0–100, derived from norm
  perThesis: ThesisMatch[];
}

export interface RankedParty extends PartyScore {
  rank: number;
}

export interface MatchResult {
  ranked: RankedParty[];
  answeredCount: number;
}

const EPSILON = 1e-9;

/**
 * Number of theses the user actually answered (answer ≠ 0 / not skipped).
 */
export function countAnswered(
  theses: Thesis[],
  answers: Record<string, AnswerRecord>,
): number {
  return theses.reduce((acc, t) => {
    const a = answers[t.id];
    return acc + (a && a.answer !== 0 ? 1 : 0);
  }, 0);
}

/** Minimum number of answered theses for a valid result. */
export const MIN_THESES = 5;

/**
 * Compute the score for a single party. Returns null when fewer than
 * MIN_THESES theses have been answered.
 */
export function computePartyScore(
  party: Party,
  theses: Thesis[],
  positions: Position[],
  answers: Record<string, AnswerRecord>,
): PartyScore | null {
  if (countAnswered(theses, answers) < MIN_THESES) return null;

  let score = 0;
  let denom = 0;
  const perThesis: ThesisMatch[] = [];

  for (const thesis of theses) {
    const ans = answers[thesis.id];
    const pos = positions.find(
      (p) => p.party_id === party.id && p.thesis_id === thesis.id,
    );

    // No answer or skipped → no contribution to score or denominator.
    if (!ans || ans.answer === 0) {
      perThesis.push({
        thesis,
        position: pos ?? null,
        userAnswer: 0,
        weighted: ans?.weighted ?? false,
        match: 0,
        weightedMatch: 0,
      });
      continue;
    }

    const sUser: UserAnswer = ans.answer;
    const sParty: number = pos?.position ?? 0;
    const w = ans.weighted ? 2 : 1;
    const match = sUser * sParty;
    const weightedMatch = match * w;

    score += weightedMatch;
    denom += w;

    perThesis.push({
      thesis,
      position: pos ?? null,
      userAnswer: sUser,
      weighted: ans.weighted,
      match,
      weightedMatch,
    });
  }

  const norm = denom > 0 ? score / denom : 0;
  const percentage = Math.round(((norm + 1) / 2) * 100);

  return { party, score, norm, percentage, perThesis };
}

/**
 * Assign competition ranks (1, 1, 3, …) to scores already sorted by norm desc,
 * ties broken alphabetically by party short_name.
 */
export function rankParties(scores: PartyScore[]): RankedParty[] {
  const sorted = [...scores].sort((a, b) => {
    if (Math.abs(b.norm - a.norm) > EPSILON) return b.norm - a.norm;
    return a.party.short_name.localeCompare(b.party.short_name, "de");
  });

  let rank = 1;
  return sorted.map((s, i) => {
    if (i > 0 && Math.abs(s.norm - sorted[i - 1].norm) > EPSILON) {
      rank = i + 1;
    }
    return { ...s, rank };
  });
}

/**
 * Full result computation. Returns null when fewer than MIN_THESES theses
 * have been answered.
 */
export function computeResults(
  parties: Party[],
  theses: Thesis[],
  positions: Position[],
  answers: Record<string, AnswerRecord>,
): MatchResult | null {
  const answeredCount = countAnswered(theses, answers);
  if (answeredCount < MIN_THESES) return null;

  const scores = parties
    .map((p) => computePartyScore(p, theses, positions, answers))
    .filter((s): s is PartyScore => s !== null);

  return { ranked: rankParties(scores), answeredCount };
}
