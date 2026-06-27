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
// Mock dataset — BTW 2025 (29 parties, 60 theses in 10 categories, 3 tiers)
// ---------------------------------------------------------------------------

const mockElection: Election = {
  id: "btw2025",
  type: "bundestag",
  date: "2025-02-23",
  region: "Bund",
  source_url: "https://www.bundeswahlleiterin.de/bundestagswahlen/2025/wahlbewerber.html",
  phase: "erfassung",
  title: "Bundestagswahl 2025",
  is_preview: true,
};

export function mockDataset(electionId: string): ElectionData {
  const election: Election = { ...mockElection, id: electionId };

  const categories = [
    { id: "cat-btw2025-wirtschaft", election_id: electionId, name: "Wirtschaft und Finanzen", description: "Wirtschaftspolitik, Haushalt, Steuern, Schulden", sort_order: 1, is_sensitive: false },
    { id: "cat-btw2025-soziales", election_id: electionId, name: "Soziales und Gesundheit", description: "Renten, Krankenversicherung, Pflege, Gesundheitsversorgung", sort_order: 2, is_sensitive: false },
    { id: "cat-btw2025-klima", election_id: electionId, name: "Klima und Umwelt", description: "Klimaschutz, Energiepolitik, Naturschutz, CO2-Reduktion", sort_order: 3, is_sensitive: false },
    { id: "cat-btw2025-bildung", election_id: electionId, name: "Bildung und Forschung", description: "Schulpolitik, Hochschulen, Forschungsförderung, Bildungsgerechtigkeit", sort_order: 4, is_sensitive: false },
    { id: "cat-btw2025-europa", election_id: electionId, name: "Europa und Außenpolitik", description: "EU-Integration, Außenhandel, Entwicklungshilfe, Sicherheit", sort_order: 5, is_sensitive: false },
    { id: "cat-btw2025-innen", election_id: electionId, name: "Innen und Recht", description: "Innere Sicherheit, Justiz, Verfassungsschutz, Polizei", sort_order: 6, is_sensitive: true },
    { id: "cat-btw2025-migration", election_id: electionId, name: "Migration und Integration", description: "Einwanderungspolitik, Asyl, Integration, Flucht", sort_order: 7, is_sensitive: true },
    { id: "cat-btw2025-demokratie", election_id: electionId, name: "Demokratie und Verfassung", description: "Demokratiequalität, Wahlrecht, Parteienfinanzierung, Bürgerrechte", sort_order: 8, is_sensitive: true },
    { id: "cat-btw2025-verkehr", election_id: electionId, name: "Verkehr und Infrastruktur", description: "Mobilität, öffentlicher Nahverkehr, Digitalinfrastruktur", sort_order: 9, is_sensitive: false },
    { id: "cat-btw2025-digital", election_id: electionId, name: "Digitales und Datenschutz", description: "Digitalisierung, Datenschutz, KI-Regulierung, Netzpolitik", sort_order: 10, is_sensitive: false },
  ];

  const parties = [
    { id: "p-spd", election_id: electionId, name: "Sozialdemokratische Partei Deutschlands", short_name: "SPD", color: "#E3000F" },
    { id: "p-cdu", election_id: electionId, name: "Christlich Demokratische Union Deutschlands", short_name: "CDU", color: "#000000" },
    { id: "p-gruene", election_id: electionId, name: "BÜNDNIS 90/DIE GRÜNEN", short_name: "GRÜNE", color: "#46A046" },
    { id: "p-fdp", election_id: electionId, name: "Freie Demokratische Partei", short_name: "FDP", color: "#FFED00" },
    { id: "p-afd", election_id: electionId, name: "Alternative für Deutschland", short_name: "AfD", color: "#009EE0" },
    { id: "p-csu", election_id: electionId, name: "Christlich-Soziale Union in Bayern e.V.", short_name: "CSU", color: "#0080C8" },
    { id: "p-die-linke", election_id: electionId, name: "Die Linke", short_name: "Die Linke", color: "#BE3075" },
    { id: "p-freie-waehler", election_id: electionId, name: "FREIE WÄHLER", short_name: "FREIE WÄHLER", color: "#FF8C00" },
    { id: "p-tierschutzpartei", election_id: electionId, name: "PARTEI MENSCH UMWELT TIERSCHUTZ", short_name: "Tierschutzpartei", color: "#7BB62E" },
    { id: "p-diebasis", election_id: electionId, name: "Basisdemokratische Partei Deutschland", short_name: "dieBasis", color: "#4B0082" },
    { id: "p-die-partei", election_id: electionId, name: "Partei für Arbeit, Rechtsstaat, Tierschutz, Elitenförderung und basisdemokratische Initiative", short_name: "Die PARTEI", color: "#722F37" },
    { id: "p-–", election_id: electionId, name: "Die Gerechtigkeitspartei – Team Todenhöfer", short_name: "–", color: "#888888" },
    { id: "p-piraten", election_id: electionId, name: "Piratenpartei Deutschland", short_name: "PIRATEN", color: "#660099" },
    { id: "p-volt", election_id: electionId, name: "Volt Deutschland", short_name: "Volt", color: "#502779" },
    { id: "p-oedp", election_id: electionId, name: "Ökologisch-Demokratische Partei", short_name: "ÖDP", color: "#FFA500" },
    { id: "p-ssw", election_id: electionId, name: "Südschleswigscher Wählerverband", short_name: "SSW", color: "#003399" },
    { id: "p-verjuengungsforschung", election_id: electionId, name: "Partei für Verjüngungsforschung", short_name: "Verjüngungsforschung", color: "#00CED1" },
    { id: "p-pdh", election_id: electionId, name: "Partei der Humanisten", short_name: "PdH", color: "#FF6600" },
    { id: "p-buendnis-c", election_id: electionId, name: "Bündnis C - Christen für Deutschland", short_name: "Bündnis C", color: "#0066CC" },
    { id: "p-bp", election_id: electionId, name: "Bayernpartei", short_name: "BP", color: "#0066CC" },
    { id: "p-mlpd", election_id: electionId, name: "Marxistisch-Leninistische Partei Deutschlands", short_name: "MLPD", color: "#FF0000" },
    { id: "p-menschliche-welt", election_id: electionId, name: "Menschliche Welt", short_name: "MENSCHLICHE WELT", color: "#FFB347" },
    { id: "p-pdf", election_id: electionId, name: "Partei des Fortschritts", short_name: "PdF", color: "#9370DB" },
    { id: "p-sgp", election_id: electionId, name: "Sozialistische Gleichheitspartei, Vierte Internationale", short_name: "SGP", color: "#DC143C" },
    { id: "p-bueso", election_id: electionId, name: "Bürgerrechtsbewegung Solidarität", short_name: "BüSo", color: "#00008B" },
    { id: "p-buendnis-deutschland", election_id: electionId, name: "BÜNDNIS DEUTSCHLAND", short_name: "BÜNDNIS DEUTSCHLAND", color: "#004B8C" },
    { id: "p-bsw", election_id: electionId, name: "Bündnis Sahra Wagenknecht - Vernunft und Gerechtigkeit", short_name: "BSW", color: "#8E2DE2" },
    { id: "p-mera25", election_id: electionId, name: "MERA25 - Gemeinsam für Europäische Unabhängigkeit", short_name: "MERA25", color: "#E50064" },
    { id: "p-werteunion", election_id: electionId, name: "WerteUnion", short_name: "WerteUnion", color: "#333333" },
  ];

  const theses = [
    { id: "the-btw2025-wirt-1", election_id: electionId, category_id: "cat-btw2025-wirtschaft", sort_order: 1, weight: 1, tier: "20", title: "Der Staat soll die", text: "Der Staat soll die Schuldenbremse beibehalten." },
    { id: "the-btw2025-wirt-2", election_id: electionId, category_id: "cat-btw2025-wirtschaft", sort_order: 2, weight: 1, tier: "20", title: "Vermögende sollen höher besteuert", text: "Vermögende sollen höher besteuert werden." },
    { id: "the-btw2025-wirt-3", election_id: electionId, category_id: "cat-btw2025-wirtschaft", sort_order: 3, weight: 1, tier: "40", title: "Die Mehrwertsteuer soll gesenkt", text: "Die Mehrwertsteuer soll gesenkt werden." },
    { id: "the-btw2025-wirt-4", election_id: electionId, category_id: "cat-btw2025-wirtschaft", sort_order: 4, weight: 1, tier: "40", title: "Der Staat soll sich", text: "Der Staat soll sich an strategisch wichtigen Unternehmen beteiligen." },
    { id: "the-btw2025-wirt-5", election_id: electionId, category_id: "cat-btw2025-wirtschaft", sort_order: 5, weight: 1, tier: "60plus", title: "Ein gesetzlicher Mindestlohn von", text: "Ein gesetzlicher Mindestlohn von 15 Euro soll gelten." },
    { id: "the-btw2025-wirt-6", election_id: electionId, category_id: "cat-btw2025-wirtschaft", sort_order: 6, weight: 1, tier: "60plus", title: "Steuervergünstigungen für Dieselkraft...", text: "Steuervergünstigungen für Dieselkraftstoff sollen abgeschafft werden." },
    { id: "the-btw2025-soz-1", election_id: electionId, category_id: "cat-btw2025-soziales", sort_order: 1, weight: 1, tier: "20", title: "Das Renteneintrittsalter soll nicht", text: "Das Renteneintrittsalter soll nicht weiter steigen." },
    { id: "the-btw2025-soz-2", election_id: electionId, category_id: "cat-btw2025-soziales", sort_order: 2, weight: 1, tier: "20", title: "Die Bürgergeld-Sätze sollen erhöht", text: "Die Bürgergeld-Sätze sollen erhöht werden." },
    { id: "the-btw2025-soz-3", election_id: electionId, category_id: "cat-btw2025-soziales", sort_order: 3, weight: 1, tier: "40", title: "Eine Kopfpauschale in der", text: "Eine Kopfpauschale in der Krankenversicherung soll eingeführt werden." },
    { id: "the-btw2025-soz-4", election_id: electionId, category_id: "cat-btw2025-soziales", sort_order: 4, weight: 1, tier: "40", title: "Pflegeleistungen sollen staatlich stä...", text: "Pflegeleistungen sollen staatlich stärker finanziert werden." },
    { id: "the-btw2025-soz-5", election_id: electionId, category_id: "cat-btw2025-soziales", sort_order: 5, weight: 1, tier: "60plus", title: "Eine Bürgerversicherung soll alle", text: "Eine Bürgerversicherung soll alle Bürger in einer Kasse erfassen." },
    { id: "the-btw2025-soz-6", election_id: electionId, category_id: "cat-btw2025-soziales", sort_order: 6, weight: 1, tier: "60plus", title: "Kinderkrankengeld soll unbefristet ge...", text: "Kinderkrankengeld soll unbefristet gezahlt werden." },
    { id: "the-btw2025-kli-1", election_id: electionId, category_id: "cat-btw2025-klima", sort_order: 1, weight: 1, tier: "20", title: "Deutschland soll bis 2035", text: "Deutschland soll bis 2035 klimaneutral sein." },
    { id: "the-btw2025-kli-2", election_id: electionId, category_id: "cat-btw2025-klima", sort_order: 2, weight: 1, tier: "20", title: "Fossile Heizungen sollen ab", text: "Fossile Heizungen sollen ab 2030 nicht mehr installiert werden." },
    { id: "the-btw2025-kli-3", election_id: electionId, category_id: "cat-btw2025-klima", sort_order: 3, weight: 1, tier: "40", title: "Ein CO2-Preis von 100", text: "Ein CO2-Preis von 100 Euro pro Tonne soll gelten." },
    { id: "the-btw2025-kli-4", election_id: electionId, category_id: "cat-btw2025-klima", sort_order: 4, weight: 1, tier: "40", title: "Atomkraftwerke sollen wieder in", text: "Atomkraftwerke sollen wieder in Betrieb genommen werden." },
    { id: "the-btw2025-kli-5", election_id: electionId, category_id: "cat-btw2025-klima", sort_order: 5, weight: 1, tier: "60plus", title: "Ein Tempolimit von 130", text: "Ein Tempolimit von 130 km/h auf Autobahnen soll gelten." },
    { id: "the-btw2025-kli-6", election_id: electionId, category_id: "cat-btw2025-klima", sort_order: 6, weight: 1, tier: "60plus", title: "Subventionen für fossile Energien", text: "Subventionen für fossile Energien sollen vollständig gestrichen werden." },
    { id: "the-btw2025-bil-1", election_id: electionId, category_id: "cat-btw2025-bildung", sort_order: 1, weight: 1, tier: "20", title: "Das Studium soll gebührenfrei", text: "Das Studium soll gebührenfrei bleiben." },
    { id: "the-btw2025-bil-2", election_id: electionId, category_id: "cat-btw2025-bildung", sort_order: 2, weight: 1, tier: "20", title: "Der Bund soll mehr", text: "Der Bund soll mehr Geld für Schulen bereitstellen." },
    { id: "the-btw2025-bil-3", election_id: electionId, category_id: "cat-btw2025-bildung", sort_order: 3, weight: 1, tier: "40", title: "Ganztagsschulen sollen zur Regel", text: "Ganztagsschulen sollen zur Regel werden." },
    { id: "the-btw2025-bil-4", election_id: electionId, category_id: "cat-btw2025-bildung", sort_order: 4, weight: 1, tier: "40", title: "Forschungsetats sollen deutlich erhöht", text: "Forschungsetats sollen deutlich erhöht werden." },
    { id: "the-btw2025-bil-5", election_id: electionId, category_id: "cat-btw2025-bildung", sort_order: 5, weight: 1, tier: "60plus", title: "Lehrpläne sollen digitale Kompetenzen", text: "Lehrpläne sollen digitale Kompetenzen verpflichtend integrieren." },
    { id: "the-btw2025-bil-6", election_id: electionId, category_id: "cat-btw2025-bildung", sort_order: 6, weight: 1, tier: "60plus", title: "Das mehrgliedige Schulsystem soll", text: "Das mehrgliedige Schulsystem soll durch ein Gesamtschulsystem ersetzt werden." },
    { id: "the-btw2025-eur-1", election_id: electionId, category_id: "cat-btw2025-europa", sort_order: 1, weight: 1, tier: "20", title: "Die EU soll eine", text: "Die EU soll eine gemeinsame Armee aufbauen." },
    { id: "the-btw2025-eur-2", election_id: electionId, category_id: "cat-btw2025-europa", sort_order: 2, weight: 1, tier: "20", title: "Militärische Unterstützung für die", text: "Militärische Unterstützung für die Ukraine soll weitergehen." },
    { id: "the-btw2025-eur-3", election_id: electionId, category_id: "cat-btw2025-europa", sort_order: 3, weight: 1, tier: "40", title: "Die EU soll weitere", text: "Die EU soll weitere Mitglieder aufnehmen." },
    { id: "the-btw2025-eur-4", election_id: electionId, category_id: "cat-btw2025-europa", sort_order: 4, weight: 1, tier: "40", title: "EU-Staaten sollen eine gemeinsame", text: "EU-Staaten sollen eine gemeinsame Außenpolitik führen." },
    { id: "the-btw2025-eur-5", election_id: electionId, category_id: "cat-btw2025-europa", sort_order: 5, weight: 1, tier: "60plus", title: "Europäische Staatsanleihen (Eurobonds...", text: "Europäische Staatsanleihen (Eurobonds) sollen eingeführt werden." },
    { id: "the-btw2025-eur-6", election_id: electionId, category_id: "cat-btw2025-europa", sort_order: 6, weight: 1, tier: "60plus", title: "Entwicklungshilfe soll auf 0,7", text: "Entwicklungshilfe soll auf 0,7 Prozent des BIP steigen." },
    { id: "the-btw2025-inn-1", election_id: electionId, category_id: "cat-btw2025-innen", sort_order: 1, weight: 1, tier: "20", title: "Die Polizei soll mehr", text: "Die Polizei soll mehr Personal erhalten." },
    { id: "the-btw2025-inn-2", election_id: electionId, category_id: "cat-btw2025-innen", sort_order: 2, weight: 1, tier: "20", title: "Videoüberwachung im öffentlichen Raum", text: "Videoüberwachung im öffentlichen Raum soll ausgeweitet werden." },
    { id: "the-btw2025-inn-3", election_id: electionId, category_id: "cat-btw2025-innen", sort_order: 3, weight: 1, tier: "40", title: "Der Verfassungsschutz soll mehr", text: "Der Verfassungsschutz soll mehr Befugnisse erhalten." },
    { id: "the-btw2025-inn-4", election_id: electionId, category_id: "cat-btw2025-innen", sort_order: 4, weight: 1, tier: "40", title: "Das Waffenrecht soll weiter", text: "Das Waffenrecht soll weiter verschärft werden." },
    { id: "the-btw2025-inn-5", election_id: electionId, category_id: "cat-btw2025-innen", sort_order: 5, weight: 1, tier: "60plus", title: "Bundeseingreiftruppen der Polizei sollen", text: "Bundeseingreiftruppen der Polizei sollen dauerhaft etabliert werden." },
    { id: "the-btw2025-inn-6", election_id: electionId, category_id: "cat-btw2025-innen", sort_order: 6, weight: 1, tier: "60plus", title: "Die Justiz soll auf", text: "Die Justiz soll auf Bundesebene zentralisiert werden." },
    { id: "the-btw2025-mig-1", election_id: electionId, category_id: "cat-btw2025-migration", sort_order: 1, weight: 1, tier: "20", title: "Deutschland soll mehr Flüchtlinge", text: "Deutschland soll mehr Flüchtlinge aufnehmen." },
    { id: "the-btw2025-mig-2", election_id: electionId, category_id: "cat-btw2025-migration", sort_order: 2, weight: 1, tier: "20", title: "Das Asylrecht soll strenger", text: "Das Asylrecht soll strenger gefasst werden." },
    { id: "the-btw2025-mig-3", election_id: electionId, category_id: "cat-btw2025-migration", sort_order: 3, weight: 1, tier: "40", title: "Familiennachzug für Geflüchtete soll", text: "Familiennachzug für Geflüchtete soll eingeschränkt werden." },
    { id: "the-btw2025-mig-4", election_id: electionId, category_id: "cat-btw2025-migration", sort_order: 4, weight: 1, tier: "40", title: "Integrationskurse sollen verpflichten...", text: "Integrationskurse sollen verpflichtend sein." },
    { id: "the-btw2025-mig-5", election_id: electionId, category_id: "cat-btw2025-migration", sort_order: 5, weight: 1, tier: "60plus", title: "Aufenthaltstitel sollen an Deutschken...", text: "Aufenthaltstitel sollen an Deutschkenntnisse gekoppelt werden." },
    { id: "the-btw2025-mig-6", election_id: electionId, category_id: "cat-btw2025-migration", sort_order: 6, weight: 1, tier: "60plus", title: "Abschiebungen bei straffälligen Geflü...", text: "Abschiebungen bei straffälligen Geflüchteten sollen konsequenter erfolgen." },
    { id: "the-btw2025-dem-1", election_id: electionId, category_id: "cat-btw2025-demokratie", sort_order: 1, weight: 1, tier: "20", title: "Das Wahlalter soll auf", text: "Das Wahlalter soll auf 16 Jahre gesenkt werden." },
    { id: "the-btw2025-dem-2", election_id: electionId, category_id: "cat-btw2025-demokratie", sort_order: 2, weight: 1, tier: "20", title: "Parteispenden sollen transparenter ge...", text: "Parteispenden sollen transparenter gemacht werden." },
    { id: "the-btw2025-dem-3", election_id: electionId, category_id: "cat-btw2025-demokratie", sort_order: 3, weight: 1, tier: "40", title: "Volksentscheide auf Bundesebene sollen", text: "Volksentscheide auf Bundesebene sollen eingeführt werden." },
    { id: "the-btw2025-dem-4", election_id: electionId, category_id: "cat-btw2025-demokratie", sort_order: 4, weight: 1, tier: "40", title: "Lobbyismus im Bundestag soll", text: "Lobbyismus im Bundestag soll strenger reguliert werden." },
    { id: "the-btw2025-dem-5", election_id: electionId, category_id: "cat-btw2025-demokratie", sort_order: 5, weight: 1, tier: "60plus", title: "Die Amtszeit des Kanzlers", text: "Die Amtszeit des Kanzlers soll auf zwei Perioden begrenzt werden." },
    { id: "the-btw2025-dem-6", election_id: electionId, category_id: "cat-btw2025-demokratie", sort_order: 6, weight: 1, tier: "60plus", title: "Abgeordnete sollen nicht in", text: "Abgeordnete sollen nicht in Aufsichtsräten von Unternehmen sitzen." },
    { id: "the-btw2025-ver-1", election_id: electionId, category_id: "cat-btw2025-verkehr", sort_order: 1, weight: 1, tier: "20", title: "Der öffentliche Personennahverkehr soll", text: "Der öffentliche Personennahverkehr soll kostenlos sein." },
    { id: "the-btw2025-ver-2", election_id: electionId, category_id: "cat-btw2025-verkehr", sort_order: 2, weight: 1, tier: "20", title: "Das Schienennetz soll stark", text: "Das Schienennetz soll stark ausgebaut werden." },
    { id: "the-btw2025-ver-3", election_id: electionId, category_id: "cat-btw2025-verkehr", sort_order: 3, weight: 1, tier: "40", title: "Die Lkw-Maut soll auf", text: "Die Lkw-Maut soll auf alle Bundesstraßen ausgeweitet werden." },
    { id: "the-btw2025-ver-4", election_id: electionId, category_id: "cat-btw2025-verkehr", sort_order: 4, weight: 1, tier: "40", title: "Radwege sollen flächendeckend ausgebaut", text: "Radwege sollen flächendeckend ausgebaut werden." },
    { id: "the-btw2025-ver-5", election_id: electionId, category_id: "cat-btw2025-verkehr", sort_order: 5, weight: 1, tier: "60plus", title: "Neue Autobahnstrecken sollen nicht", text: "Neue Autobahnstrecken sollen nicht mehr gebaut werden." },
    { id: "the-btw2025-ver-6", election_id: electionId, category_id: "cat-btw2025-verkehr", sort_order: 6, weight: 1, tier: "60plus", title: "Die Lkw-Maut soll verdoppelt", text: "Die Lkw-Maut soll verdoppelt werden." },
    { id: "the-btw2025-dig-1", election_id: electionId, category_id: "cat-btw2025-digital", sort_order: 1, weight: 1, tier: "20", title: "Schnelles Internet soll flächendeckend", text: "Schnelles Internet soll flächendeckend staatlich gefördert werden." },
    { id: "the-btw2025-dig-2", election_id: electionId, category_id: "cat-btw2025-digital", sort_order: 2, weight: 1, tier: "20", title: "Behördenleistungen sollen vollständig...", text: "Behördenleistungen sollen vollständig digital verfügbar sein." },
    { id: "the-btw2025-dig-3", election_id: electionId, category_id: "cat-btw2025-digital", sort_order: 3, weight: 1, tier: "40", title: "Künstliche Intelligenz soll staatlich", text: "Künstliche Intelligenz soll staatlich reguliert werden." },
    { id: "the-btw2025-dig-4", election_id: electionId, category_id: "cat-btw2025-digital", sort_order: 4, weight: 1, tier: "40", title: "Ein Recht auf digitale", text: "Ein Recht auf digitale Grundversorgung (Internet) soll gelten." },
    { id: "the-btw2025-dig-5", election_id: electionId, category_id: "cat-btw2025-digital", sort_order: 5, weight: 1, tier: "60plus", title: "Gesichtserkennung an Bahnhöfen soll", text: "Gesichtserkennung an Bahnhöfen soll erlaubt sein." },
    { id: "the-btw2025-dig-6", election_id: electionId, category_id: "cat-btw2025-digital", sort_order: 6, weight: 1, tier: "60plus", title: "Ende-zu-Ende-Verschlüsselung soll für...", text: "Ende-zu-Ende-Verschlüsselung soll für Strafverfolgung durchbrochen werden dürfen." },
  ];

  const positions: PositionType[] = [];
  // Placeholder positions — will be replaced with real data from KI extraction
  for (const party of parties) {
    for (const thesis of theses) {
      positions.push({
        id: `pos-${party.id}-${thesis.id}`,
        party_id: party.id,
        thesis_id: thesis.id,
        position: 0, // neutral placeholder
        rationale: "",
        source_quote: "",
        source_url: "",
      });
    }
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

## Thesen-Modell

Die Thesen sind in drei Fassungen gestaffelt:
- **20er-Set**: 20 Kern-Thesen, die alle Rubriken abdecken
- **40er-Set**: 20 + 20 tiefere Thesen
- **60+-Set**: 40 + 20+ Detailthesen

## Datenerfassung

Parteipositionen werden aus Wahlprogrammen extrahiert. Jede Position ist mit einem **Beleg** (Zitat + Quelle) verknüpft.

## KI-Transparenz

> ⚠️ **KI-Transparenzhinweis:** Bei der Extraktion von Positionen aus Wahlprogrammen kommen automatisierte Verfahren (LLM-basierte KI-Extraktion) zum Einsatz. Alle KI-generierten Positionen werden vor Veröffentlichung von einem Review-Prozess geprüft.
`;