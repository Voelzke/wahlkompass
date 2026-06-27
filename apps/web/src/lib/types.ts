// Core domain types for the Wahlkompass matching tool.

export type ElectionType = "bundestag" | "landtag" | "europawahl" | "kommunal";

export type ElectionPhase = "erfassung" | "live" | "archiv";

export interface Election {
  id: string;
  type: ElectionType;
  date: string; // ISO 8601 date (YYYY-MM-DD)
  region: string;
  source_url?: string;
  phase: ElectionPhase;
  title?: string;
  /** True when not all parties / positions have been captured yet. */
  is_preview?: boolean;
}

export interface Category {
  id: string;
  election_id: string;
  name: string;
  description: string;
  sort_order: number;
  is_sensitive: boolean;
}

export interface Party {
  id: string;
  election_id: string;
  name: string;
  short_name: string;
  color: string; // hex, e.g. "#E3000F"
  logo_url?: string;
  program_url?: string;
}

export interface Thesis {
  id: string;
  election_id: string;
  category_id: string;
  title: string;
  text: string;
  sort_order: number;
  /** Base weight for this thesis (default 1). */
  weight: number;
}

/** A party's position on a single thesis. */
export interface Position {
  id: string;
  party_id: string;
  thesis_id: string;
  /** +1 = zustimmend, -1 = ablehnend, 0 = neutral / keine Aussage */
  position: 1 | -1 | 0;
  rationale?: string;
  source_quote?: string;
  source_url?: string;
}

/** The user's answer to a thesis. */
export type UserAnswer = 1 | -1 | 0;

export interface AnswerRecord {
  /** +1 zustimmen, -1 ablehnen, 0 überspringen */
  answer: UserAnswer;
  /** Doppelte Gewichtung toggled by the user. */
  weighted: boolean;
}

export interface ElectionData {
  election: Election;
  categories: Category[];
  parties: Party[];
  theses: Thesis[];
  positions: Position[];
}

/** Tier options for the matching flow. */
export interface Tier {
  id: "kurz" | "mittel" | "lang";
  label: string;
  count: number;
}
