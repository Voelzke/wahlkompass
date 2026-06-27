/**
 * API client for the Wahlkompass.
 *
 * Fetches election data from NEXT_PUBLIC_API_URL when available. When the API
 * is unreachable (e.g. during local development / tests / no backend running)
 * a built-in mock dataset for BTW 2025 is returned so the app stays usable.
 */

import type { ElectionData, Election, Position as PositionType } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { Accept: "application/json" },
    // Prevent Next.js from caching during development.
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${path}`);
  return (await res.json()) as T;
}

export async function getElections(): Promise<Election[]> {
  if (API_URL) {
    try {
      return await fetchJson<Election[]>("/api/elections");
    } catch {
      // fall through to mock
    }
  }
  return [mockElection];
}

export async function getElectionData(electionId: string): Promise<ElectionData> {
  if (API_URL) {
    try {
      return await fetchJson<ElectionData>(`/api/elections/${electionId}`);
    } catch {
      // fall through to mock
    }
  }
  return mockDataset(electionId);
}

export async function getMethodik(): Promise<string> {
  if (API_URL) {
    try {
      return await fetchJson<string>("/api/methodik");
    } catch {
      // fall through
    }
  }
  return MOCK_METHODIK;
}

// ---------------------------------------------------------------------------
// Mock dataset — BTW 2025 (simplified, for development without a backend)
// ---------------------------------------------------------------------------

const mockElection: Election = {
  id: "btw2025",
  type: "bundestag",
  date: "2025-02-23",
  region: "Bund",
  source_url:
    "https://www.bundeswahlleiter.de/bundestagswahlen/2025/unterlagen/landeslisten.html",
  phase: "erfassung",
  title: "Bundestagswahl 2025",
  is_preview: true,
};

export function mockDataset(electionId: string): ElectionData {
  const election: Election = { ...mockElection, id: electionId };

  const categories = [
    {
      id: "cat-klima",
      election_id: electionId,
      name: "Klima und Umwelt",
      description: "Klimaschutz, Energiepolitik, Naturschutz",
      sort_order: 1,
      is_sensitive: false,
    },
    {
      id: "cat-wirtschaft",
      election_id: electionId,
      name: "Wirtschaft und Finanzen",
      description: "Wirtschaftspolitik, Haushalt, Steuern",
      sort_order: 2,
      is_sensitive: false,
    },
    {
      id: "cat-soziales",
      election_id: electionId,
      name: "Soziales und Gesundheit",
      description: "Renten, Krankenversicherung, Pflege",
      sort_order: 3,
      is_sensitive: false,
    },
    {
      id: "cat-migration",
      election_id: electionId,
      name: "Migration und Integration",
      description: "Einwanderungspolitik, Asyl, Integration",
      sort_order: 4,
      is_sensitive: true,
    },
    {
      id: "cat-bildung",
      election_id: electionId,
      name: "Bildung und Forschung",
      description: "Schulpolitik, Hochschulen, Forschung",
      sort_order: 5,
      is_sensitive: false,
    },
  ];

  const parties = [
    { id: "p-spd", election_id: electionId, name: "SPD", short_name: "SPD", color: "#E3000F" },
    { id: "p-cdu", election_id: electionId, name: "CDU/CSU", short_name: "CDU", color: "#000000" },
    { id: "p-gruene", election_id: electionId, name: "Bündnis 90/Die Grünen", short_name: "Grüne", color: "#46962B" },
    { id: "p-fdp", election_id: electionId, name: "FDP", short_name: "FDP", color: "#FFED00" },
    { id: "p-afd", election_id: electionId, name: "AfD", short_name: "AfD", color: "#009EE0" },
    { id: "p-linke", election_id: electionId, name: "Die Linke", short_name: "Linke", color: "#BE3075" },
    { id: "p-bsw", election_id: electionId, name: "BSW", short_name: "BSW", color: "#EAB614" },
    { id: "p-volt", election_id: electionId, name: "Volt", short_name: "Volt", color: "#502779" },
  ];

  const theses = [
    { id: "t1", election_id: electionId, category_id: "cat-klima", sort_order: 1, weight: 1, title: "Klimaneutralität bis 2040", text: "Deutschland soll bis 2040 klimaneutral werden." },
    { id: "t2", election_id: electionId, category_id: "cat-klima", sort_order: 2, weight: 1, title: "Atomenergie", text: "Die Laufzeiten bestehender Kernkraftwerke sollen verlängert werden." },
    { id: "t3", election_id: electionId, category_id: "cat-wirtschaft", sort_order: 3, weight: 1, title: "Schuldenbremse", text: "Die Schuldenbremse soll in der jetzigen Form beibehalten werden." },
    { id: "t4", election_id: electionId, category_id: "cat-wirtschaft", sort_order: 4, weight: 1, title: "Reichensteuer", text: "Steuern für hohe Einkommen und Vermögen sollen steigen." },
    { id: "t5", election_id: electionId, category_id: "cat-soziales", sort_order: 5, weight: 1, title: "Bürgerversicherung", text: "Es soll eine einheitliche Bürgerversicherung für alle geben." },
    { id: "t6", election_id: electionId, category_id: "cat-soziales", sort_order: 6, weight: 1, title: "Renteneintrittsalter", text: "Das Renteneintrittsalter soll weiter steigen." },
    { id: "t7", election_id: electionId, category_id: "cat-migration", sort_order: 7, weight: 1, title: "Asylbewerberleistungsgesetz", text: "Asylsuchende sollen Sachleistungen statt Geld bekommen." },
    { id: "t8", election_id: electionId, category_id: "cat-migration", sort_order: 8, weight: 1, title: "Familiennachzug", text: "Der Familiennachzug für Geflüchtete soll stärker eingeschränkt werden." },
    { id: "t9", election_id: electionId, category_id: "cat-bildung", sort_order: 9, weight: 1, title: "Elternbeiträge Kita", text: "Kitas sollen bundesweit beitragsfrei sein." },
    { id: "t10", election_id: electionId, category_id: "cat-bildung", sort_order: 10, weight: 1, title: "Bundesländerfinanzierung", text: "Die Hochschulausstattung soll stärker vom Bund finanziert werden." },
  ];

  // Party positions matrix: [party][thesis]
  // +1 zustimmend, -1 ablehnend, 0 neutral
  const pos: Record<string, number[]> = {
    "p-spd":    [ 1, -1, -1,  1,  1, -1,  0, -1,  1,  1],
    "p-cdu":    [-1,  1,  1, -1, -1,  1,  0,  1, -1, -1],
    "p-gruene": [ 1, -1, -1,  1,  1, -1,  0, -1,  1,  1],
    "p-fdp":    [-1,  1,  1, -1, -1,  1,  0,  0,  0,  1],
    "p-afd":    [-1,  1,  1, -1, -1,  1,  1,  1, -1, -1],
    "p-linke":  [ 1, -1, -1,  1,  1, -1,  0, -1,  1,  1],
    "p-bsw":    [ 1,  0, -1,  1,  1, -1,  0,  1,  0,  0],
    "p-volt":   [ 1, -1, -1,  1,  1, -1,  0, -1,  1,  1],
  };

  const positions: PositionType[] = [];
  for (const party of parties) {
    const row = pos[party.id];
    theses.forEach((thesis, i) => {
      const p = row[i] as 1 | -1 | 0;
      positions.push({
        id: `pos-${party.id}-${thesis.id}`,
        party_id: party.id,
        thesis_id: thesis.id,
        position: p,
        rationale: "",
        source_quote: "",
        source_url: "",
      });
    });
  }

  return { election, categories, parties, theses, positions };
}

const MOCK_METHODIK = `# Methodik — Wahlkompass

## Matching-Verfahren

Der Wahlkompass vergleicht Ihre Antworten zu einzelnen Thesen mit den Positionen der Parteien.

### Berechnung

- Für jede These wird ein **Match-Wert** berechnet: stimmen Sie und die Partei überein (beide zustimmen oder beide ablehnen), ist der Wert +1. Stimmen Sie nicht überein, ist er −1.
- Mit der Funktion **„doppelte Gewichtung"** können Sie einer These doppeltes Gewicht geben (Faktor 2).
- Die **Normierung** erfolgt über alle beantworteten (nicht übersprungenen Thesen): so liegt das Ergebnis immer zwischen −1 und +1 (+100 % bzw. 0 %).

## Datenerfassung

Parteipositionen werden aus Wahlprogrammen und öffentlichen Stellungnahmen extrahiert. Jede Position ist mit einem **Beleg** (Zitat + Quelle) verknüpft.

## KI-Transparenz

> ⚠️ **KI-Transparenzhinweis:** Bei der Extraktion von Positionen aus Wahlprogrammen kommen automatisierte Verfahren (LLM-basierte KI-Extraktion) zum Einsatz. Alle KI-generierten Positionen werden vor Veröffentlichung von einem Review-Prozess geprüft.
`;
