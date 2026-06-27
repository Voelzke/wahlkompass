import { describe, it, expect } from "vitest";
import {
  computePartyScore,
  computeResults,
  rankParties,
  countAnswered,
  MIN_THESES,
  type PartyScore,
} from "./matching";
import type {
  Party,
  Thesis,
  Position,
  AnswerRecord,
} from "./types";

// ---------------------------------------------------------------------------
// Helpers to build test fixtures
// ---------------------------------------------------------------------------

function makeThesis(id: string, sort = 1): Thesis {
  return {
    id,
    election_id: "e1",
    category_id: "c1",
    title: `Thesis ${id}`,
    text: `Text ${id}`,
    sort_order: sort,
    weight: 1,
  };
}

function makeParty(id: string, short = id): Party {
  return {
    id,
    election_id: "e1",
    name: `Party ${id}`,
    short_name: short,
    color: "#000000",
  };
}

function pos(
  partyId: string,
  thesisId: string,
  position: 1 | -1 | 0,
): Position {
  return {
    id: `${partyId}-${thesisId}`,
    party_id: partyId,
    thesis_id: thesisId,
    position,
  };
}

function ans(answer: 1 | -1 | 0, weighted = false): AnswerRecord {
  return { answer, weighted };
}

const theses = Array.from({ length: 6 }, (_, i) =>
  makeThesis(`t${i + 1}`, i + 1),
);

// ---------------------------------------------------------------------------
// countAnswered
// ---------------------------------------------------------------------------

describe("countAnswered", () => {
  it("counts only non-zero answers", () => {
    const answers: Record<string, AnswerRecord> = {
      t1: ans(1),
      t2: ans(-1),
      t3: ans(0),
      t4: ans(1),
    };
    expect(countAnswered(theses, answers)).toBe(3);
  });

  it("returns 0 for empty answers", () => {
    expect(countAnswered(theses, {})).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// computePartyScore — basic cases
// ---------------------------------------------------------------------------

describe("computePartyScore", () => {
  it("returns null when fewer than MIN_THESES answered", () => {
    const answers: Record<string, AnswerRecord> = {
      t1: ans(1),
      t2: ans(-1),
      t3: ans(1),
      t4: ans(-1),
    };
    expect(computePartyScore(makeParty("p1"), theses, [], answers)).toBeNull();
  });

  it("returns a score when exactly MIN_THESES answered", () => {
    const answers: Record<string, AnswerRecord> = {
      t1: ans(1),
      t2: ans(-1),
      t3: ans(1),
      t4: ans(-1),
      t5: ans(1),
    };
    const result = computePartyScore(makeParty("p1"), theses, [], answers);
    expect(result).not.toBeNull();
    expect(result!.answeredCount ?? countAnswered(theses, answers)).toBe(5);
  });

  it("returns norm +1 when party fully agrees (no weighting)", () => {
    const party = makeParty("p1");
    const positions = [
      pos("p1", "t1", 1),
      pos("p1", "t2", -1), // user -1, party -1 → agree
      pos("p1", "t3", 1),
      pos("p1", "t4", -1),
      pos("p1", "t5", 1),
      pos("p1", "t6", 1),
    ];
    const answers: Record<string, AnswerRecord> = {
      t1: ans(1),
      t2: ans(-1),
      t3: ans(1),
      t4: ans(-1),
      t5: ans(1),
      t6: ans(1),
    };
    const result = computePartyScore(party, theses, positions, answers)!;
    expect(result.norm).toBeCloseTo(1, 10);
    expect(result.percentage).toBe(100);
    expect(result.score).toBe(6); // 6 matches × weight 1
  });

  it("returns norm -1 when party fully disagrees", () => {
    const party = makeParty("p1");
    const positions = [
      pos("p1", "t1", -1),
      pos("p1", "t2", 1),
      pos("p1", "t3", -1),
      pos("p1", "t4", 1),
      pos("p1", "t5", -1),
      pos("p1", "t6", -1),
    ];
    const answers: Record<string, AnswerRecord> = {
      t1: ans(1),
      t2: ans(-1),
      t3: ans(1),
      t4: ans(-1),
      t5: ans(1),
      t6: ans(1),
    };
    const result = computePartyScore(party, theses, positions, answers)!;
    expect(result.norm).toBeCloseTo(-1, 10);
    expect(result.percentage).toBe(0);
    expect(result.score).toBe(-6);
  });

  it("returns norm 0 (50%) for neutral party positions", () => {
    const party = makeParty("p1");
    const positions = theses.map((t) => pos("p1", t.id, 0));
    const answers: Record<string, AnswerRecord> = {
      t1: ans(1),
      t2: ans(-1),
      t3: ans(1),
      t4: ans(-1),
      t5: ans(1),
      t6: ans(1),
    };
    const result = computePartyScore(party, theses, positions, answers)!;
    expect(result.norm).toBeCloseTo(0, 10);
    expect(result.percentage).toBe(50);
    expect(result.score).toBe(0);
  });

  it("skipped theses do not affect score or denominator", () => {
    const party = makeParty("p1");
    const positions = [pos("p1", "t1", 1), pos("p1", "t2", -1)];
    // 5 answered agree, 1 skipped (t6)
    const answers: Record<string, AnswerRecord> = {
      t1: ans(1),
      t2: ans(-1),
      t3: ans(1),
      t4: ans(-1),
      t5: ans(1),
      t6: ans(0),
    };
    const result = computePartyScore(party, theses, positions, answers)!;
    // Only t1–t5 contribute; t1 agree (+1), t2 agree (+1) → score 2, denom 5
    expect(result.score).toBe(2);
    expect(result.norm).toBeCloseTo(2 / 5, 10);
    expect(result.percentage).toBe(Math.round(((2 / 5 + 1) / 2) * 100));
  });
});

// ---------------------------------------------------------------------------
// Weighting
// ---------------------------------------------------------------------------

describe("doppelte Gewichtung (weighting)", () => {
  it("doubles the contribution of a weighted thesis", () => {
    const party = makeParty("p1");
    const positions = theses.map((t) => pos("p1", t.id, 1));
    const answers: Record<string, AnswerRecord> = {
      t1: ans(1, true), // weighted → w=2
      t2: ans(1),
      t3: ans(1),
      t4: ans(1),
      t5: ans(1),
      t6: ans(1),
    };
    const result = computePartyScore(party, theses, positions, answers)!;
    // All agree. denom = 2 + 1*5 = 7, score = 2 + 5 = 7 → norm 1
    expect(result.score).toBe(7);
    expect(result.norm).toBeCloseTo(1, 10);
    expect(result.percentage).toBe(100);
  });

  it("weighted disagreement has double negative impact", () => {
    const party = makeParty("p1");
    const positions = theses.map((t) => pos("p1", t.id, 1));
    const answers: Record<string, AnswerRecord> = {
      t1: ans(-1, true), // weighted disagreement → -2
      t2: ans(1),
      t3: ans(1),
      t4: ans(1),
      t5: ans(1),
      t6: ans(1),
    };
    const result = computePartyScore(party, theses, positions, answers)!;
    // score = -2 + 5 = 3, denom = 2 + 5 = 7 → norm 3/7
    expect(result.score).toBe(3);
    expect(result.norm).toBeCloseTo(3 / 7, 10);
  });

  it("perThesis records correct weighted values", () => {
    const party = makeParty("p1");
    const positions = [pos("p1", "t1", 1)];
    const answers: Record<string, AnswerRecord> = {
      t1: ans(1, true),
      t2: ans(-1),
      t3: ans(1),
      t4: ans(-1),
      t5: ans(1),
    };
    const result = computePartyScore(party, theses, positions, answers)!;
    const t1Match = result.perThesis.find((m) => m.thesis.id === "t1")!;
    expect(t1Match.weighted).toBe(true);
    expect(t1Match.match).toBe(1);
    expect(t1Match.weightedMatch).toBe(2);
  });
});

// ---------------------------------------------------------------------------
// rankParties
// ---------------------------------------------------------------------------

describe("rankParties", () => {
  function score(
    party: Party,
    norm: number,
    score = 0,
    percentage = Math.round(((norm + 1) / 2) * 100),
  ): PartyScore {
    return { party, score, norm, percentage, perThesis: [] };
  }

  it("assigns rank 1 to the highest norm, sorted descending", () => {
    const scores = [
      score(makeParty("a", "Alpha"), 0.5),
      score(makeParty("b", "Beta"), 0.8),
      score(makeParty("c", "Gamma"), 0.3),
    ];
    const ranked = rankParties(scores);
    expect(ranked[0].party.id).toBe("b");
    expect(ranked[0].rank).toBe(1);
    expect(ranked[1].party.id).toBe("a");
    expect(ranked[1].rank).toBe(2);
    expect(ranked[2].party.id).toBe("c");
    expect(ranked[2].rank).toBe(3);
  });

  it("gives tied parties the same rank and skips subsequent ranks", () => {
    const scores = [
      score(makeParty("a", "Alpha"), 0.5),
      score(makeParty("b", "Beta"), 0.5),
      score(makeParty("c", "Gamma"), 0.3),
    ];
    const ranked = rankParties(scores);
    expect(ranked[0].rank).toBe(1);
    expect(ranked[1].rank).toBe(1);
    expect(ranked[2].rank).toBe(3);
  });

  it("breaks ties alphabetically by short_name", () => {
    const scores = [
      score(makeParty("z", "Zeta"), 0.5),
      score(makeParty("a", "Alpha"), 0.5),
      score(makeParty("m", "Mu"), 0.5),
    ];
    const ranked = rankParties(scores);
    expect(ranked.map((r) => r.party.short_name)).toEqual([
      "Alpha",
      "Mu",
      "Zeta",
    ]);
    expect(ranked.every((r) => r.rank === 1)).toBe(true);
  });

  it("handles three-way tie at top then gap", () => {
    const scores = [
      score(makeParty("a"), 0.9),
      score(makeParty("b"), 0.9),
      score(makeParty("c"), 0.9),
      score(makeParty("d"), 0.1),
    ];
    const ranked = rankParties(scores);
    expect(ranked[0].rank).toBe(1);
    expect(ranked[1].rank).toBe(1);
    expect(ranked[2].rank).toBe(1);
    expect(ranked[3].rank).toBe(4);
  });
});

// ---------------------------------------------------------------------------
// computeResults (integration)
// ---------------------------------------------------------------------------

describe("computeResults", () => {
  it("returns null when fewer than MIN_THESES answered", () => {
    const parties = [makeParty("p1")];
    const answers: Record<string, AnswerRecord> = {
      t1: ans(1),
      t2: ans(-1),
    };
    expect(
      computeResults(parties, theses, [], answers),
    ).toBeNull();
  });

  it("returns ranked parties sorted by norm descending", () => {
    const pA = makeParty("a", "Alpha");
    const pB = makeParty("b", "Beta");
    const theses6 = theses;
    const positions = [
      // Party A: agrees with user on all → norm 1
      ...theses6.map((t) => pos("a", t.id, 1)),
      // Party B: agrees on 3, disagrees on 3 → norm 0
      pos("b", "t1", 1),
      pos("b", "t2", 1),
      pos("b", "t3", 1),
      pos("b", "t4", -1),
      pos("b", "t5", -1),
      pos("b", "t6", -1),
    ];
    const answers: Record<string, AnswerRecord> = {
      t1: ans(1),
      t2: ans(1),
      t3: ans(1),
      t4: ans(1),
      t5: ans(1),
      t6: ans(1),
    };
    const result = computeResults([pA, pB], theses6, positions, answers)!;
    expect(result.answeredCount).toBe(6);
    expect(result.ranked[0].party.id).toBe("a");
    expect(result.ranked[0].rank).toBe(1);
    expect(result.ranked[1].party.id).toBe("b");
    expect(result.ranked[1].rank).toBe(2);
  });

  it("parties with missing positions are treated as neutral (0)", () => {
    const party = makeParty("p1");
    // No positions at all → all s_party = 0 → norm 0, percentage 50
    const answers: Record<string, AnswerRecord> = {
      t1: ans(1),
      t2: ans(-1),
      t3: ans(1),
      t4: ans(-1),
      t5: ans(1),
      t6: ans(1),
    };
    const result = computePartyScore(party, theses, [], answers)!;
    expect(result.norm).toBeCloseTo(0, 10);
    expect(result.percentage).toBe(50);
  });

  it("MIN_THESES equals 5", () => {
    expect(MIN_THESES).toBe(5);
  });
});

// ---------------------------------------------------------------------------
// Percentage mapping
// ---------------------------------------------------------------------------

describe("percentage mapping", () => {
  it("maps norm +1 → 100%, 0 → 50%, -1 → 0%", () => {
    const party = makeParty("p1");
    const positions1 = theses.map((t) => pos("p1", t.id, 1));
    const answers: Record<string, AnswerRecord> = {
      t1: ans(1),
      t2: ans(1),
      t3: ans(1),
      t4: ans(1),
      t5: ans(1),
      t6: ans(1),
    };
    expect(
      computePartyScore(party, theses, positions1, answers)!.percentage,
    ).toBe(100);

    const positionsNeg = theses.map((t) => pos("p1", t.id, -1));
    expect(
      computePartyScore(party, theses, positionsNeg, answers)!.percentage,
    ).toBe(0);

    const positionsNeutral = theses.map((t) => pos("p1", t.id, 0));
    expect(
      computePartyScore(party, theses, positionsNeutral, answers)!.percentage,
    ).toBe(50);
  });

  it("agreement on 6 of 10 → 60%", () => {
    const theses10 = Array.from({ length: 10 }, (_, i) =>
      makeThesis(`u${i + 1}`, i + 1),
    );
    const party = makeParty("p1");
    const answers: Record<string, AnswerRecord> = {};
    const positions: Position[] = [];
    // 6 agree, 4 disagree
    theses10.forEach((t, i) => {
      answers[t.id] = ans(1);
      positions.push(pos("p1", t.id, i < 6 ? 1 : -1));
    });
    const result = computePartyScore(party, theses10, positions, answers)!;
    expect(result.norm).toBeCloseTo(0.2, 10);
    expect(result.percentage).toBe(60);
  });
});
