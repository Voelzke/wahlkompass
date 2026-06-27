-- Seed: 60+ Thesen für BTW 2025
-- 10 Rubriken × 6 Thesen = 60 Thesen
-- tier=20 (20er-Set), tier=40 (40er-Set), tier=60plus (60+-Set)

-- ============================================================
-- Wirtschaft und Finanzen
-- ============================================================
INSERT INTO thesis (id, election_id, category_id, statement, tier, weightable, sort_order, created_at, updated_at) VALUES
('the-btw2025-wirt-1', 'btw2025', 'cat-btw2025-wirtschaft', 'Der Staat soll die Schuldenbremse beibehalten.', '20', true, 1, NOW(), NOW()),
('the-btw2025-wirt-2', 'btw2025', 'cat-btw2025-wirtschaft', 'Vermögende sollen höher besteuert werden.', '20', true, 2, NOW(), NOW()),
('the-btw2025-wirt-3', 'btw2025', 'cat-btw2025-wirtschaft', 'Die Mehrwertsteuer soll gesenkt werden.', '40', true, 3, NOW(), NOW()),
('the-btw2025-wirt-4', 'btw2025', 'cat-btw2025-wirtschaft', 'Der Staat soll sich an strategisch wichtigen Unternehmen beteiligen.', '40', true, 4, NOW(), NOW()),
('the-btw2025-wirt-5', 'btw2025', 'cat-btw2025-wirtschaft', 'Ein gesetzlicher Mindestlohn von 15 Euro soll gelten.', '60plus', true, 5, NOW(), NOW()),
('the-btw2025-wirt-6', 'btw2025', 'cat-btw2025-wirtschaft', 'Steuervergünstigungen für Dieselkraftstoff sollen abgeschafft werden.', '60plus', true, 6, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- Soziales und Gesundheit
-- ============================================================
INSERT INTO thesis (id, election_id, category_id, statement, tier, weightable, sort_order, created_at, updated_at) VALUES
('the-btw2025-soz-1', 'btw2025', 'cat-btw2025-soziales', 'Das Renteneintrittsalter soll nicht weiter steigen.', '20', true, 1, NOW(), NOW()),
('the-btw2025-soz-2', 'btw2025', 'cat-btw2025-soziales', 'Die Bürgergeld-Sätze sollen erhöht werden.', '20', true, 2, NOW(), NOW()),
('the-btw2025-soz-3', 'btw2025', 'cat-btw2025-soziales', 'Eine Kopfpauschale in der Krankenversicherung soll eingeführt werden.', '40', true, 3, NOW(), NOW()),
('the-btw2025-soz-4', 'btw2025', 'cat-btw2025-soziales', 'Pflegeleistungen sollen staatlich stärker finanziert werden.', '40', true, 4, NOW(), NOW()),
('the-btw2025-soz-5', 'btw2025', 'cat-btw2025-soziales', 'Eine Bürgerversicherung soll alle Bürger in einer Kasse erfassen.', '60plus', true, 5, NOW(), NOW()),
('the-btw2025-soz-6', 'btw2025', 'cat-btw2025-soziales', 'Kinderkrankengeld soll unbefristet gezahlt werden.', '60plus', true, 6, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- Klima und Umwelt
-- ============================================================
INSERT INTO thesis (id, election_id, category_id, statement, tier, weightable, sort_order, created_at, updated_at) VALUES
('the-btw2025-kli-1', 'btw2025', 'cat-btw2025-klima', 'Deutschland soll bis 2035 klimaneutral sein.', '20', true, 1, NOW(), NOW()),
('the-btw2025-kli-2', 'btw2025', 'cat-btw2025-klima', 'Fossile Heizungen sollen ab 2030 nicht mehr installiert werden.', '20', true, 2, NOW(), NOW()),
('the-btw2025-kli-3', 'btw2025', 'cat-btw2025-klima', 'Ein CO2-Preis von 100 Euro pro Tonne soll gelten.', '40', true, 3, NOW(), NOW()),
('the-btw2025-kli-4', 'btw2025', 'cat-btw2025-klima', 'Atomkraftwerke sollen wieder in Betrieb genommen werden.', '40', true, 4, NOW(), NOW()),
('the-btw2025-kli-5', 'btw2025', 'cat-btw2025-klima', 'Ein Tempolimit von 130 km/h auf Autobahnen soll gelten.', '60plus', true, 5, NOW(), NOW()),
('the-btw2025-kli-6', 'btw2025', 'cat-btw2025-klima', 'Subventionen für fossile Energien sollen vollständig gestrichen werden.', '60plus', true, 6, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- Bildung und Forschung
-- ============================================================
INSERT INTO thesis (id, election_id, category_id, statement, tier, weightable, sort_order, created_at, updated_at) VALUES
('the-btw2025-bil-1', 'btw2025', 'cat-btw2025-bildung', 'Das Studium soll gebührenfrei bleiben.', '20', true, 1, NOW(), NOW()),
('the-btw2025-bil-2', 'btw2025', 'cat-btw2025-bildung', 'Der Bund soll mehr Geld für Schulen bereitstellen.', '20', true, 2, NOW(), NOW()),
('the-btw2025-bil-3', 'btw2025', 'cat-btw2025-bildung', 'Ganztagsschulen sollen zur Regel werden.', '40', true, 3, NOW(), NOW()),
('the-btw2025-bil-4', 'btw2025', 'cat-btw2025-bildung', 'Forschungsetats sollen deutlich erhöht werden.', '40', true, 4, NOW(), NOW()),
('the-btw2025-bil-5', 'btw2025', 'cat-btw2025-bildung', 'Lehrpläne sollen digitale Kompetenzen verpflichtend integrieren.', '60plus', true, 5, NOW(), NOW()),
('the-btw2025-bil-6', 'btw2025', 'cat-btw2025-bildung', 'Das mehrgliedige Schulsystem soll durch ein Gesamtschulsystem ersetzt werden.', '60plus', true, 6, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- Europa und Außenpolitik
-- ============================================================
INSERT INTO thesis (id, election_id, category_id, statement, tier, weightable, sort_order, created_at, updated_at) VALUES
('the-btw2025-eur-1', 'btw2025', 'cat-btw2025-europa', 'Die EU soll eine gemeinsame Armee aufbauen.', '20', true, 1, NOW(), NOW()),
('the-btw2025-eur-2', 'btw2025', 'cat-btw2025-europa', 'Militärische Unterstützung für die Ukraine soll weitergehen.', '20', true, 2, NOW(), NOW()),
('the-btw2025-eur-3', 'btw2025', 'cat-btw2025-europa', 'Die EU soll weitere Mitglieder aufnehmen.', '40', true, 3, NOW(), NOW()),
('the-btw2025-eur-4', 'btw2025', 'cat-btw2025-europa', 'EU-Staaten sollen eine gemeinsame Außenpolitik führen.', '40', true, 4, NOW(), NOW()),
('the-btw2025-eur-5', 'btw2025', 'cat-btw2025-europa', 'Europäische Staatsanleihen (Eurobonds) sollen eingeführt werden.', '60plus', true, 5, NOW(), NOW()),
('the-btw2025-eur-6', 'btw2025', 'cat-btw2025-europa', 'Entwicklungshilfe soll auf 0,7 Prozent des BIP steigen.', '60plus', true, 6, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- Innen und Recht (sensible Rubrik)
-- ============================================================
INSERT INTO thesis (id, election_id, category_id, statement, tier, weightable, sort_order, created_at, updated_at) VALUES
('the-btw2025-inn-1', 'btw2025', 'cat-btw2025-innen', 'Die Polizei soll mehr Personal erhalten.', '20', true, 1, NOW(), NOW()),
('the-btw2025-inn-2', 'btw2025', 'cat-btw2025-innen', 'Videoüberwachung im öffentlichen Raum soll ausgeweitet werden.', '20', true, 2, NOW(), NOW()),
('the-btw2025-inn-3', 'btw2025', 'cat-btw2025-innen', 'Der Verfassungsschutz soll mehr Befugnisse erhalten.', '40', true, 3, NOW(), NOW()),
('the-btw2025-inn-4', 'btw2025', 'cat-btw2025-innen', 'Das Waffenrecht soll weiter verschärft werden.', '40', true, 4, NOW(), NOW()),
('the-btw2025-inn-5', 'btw2025', 'cat-btw2025-innen', 'Bundeseingreiftruppen der Polizei sollen dauerhaft etabliert werden.', '60plus', true, 5, NOW(), NOW()),
('the-btw2025-inn-6', 'btw2025', 'cat-btw2025-innen', 'Die Justiz soll auf Bundesebene zentralisiert werden.', '60plus', true, 6, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- Migration und Integration (sensible Rubrik)
-- ============================================================
INSERT INTO thesis (id, election_id, category_id, statement, tier, weightable, sort_order, created_at, updated_at) VALUES
('the-btw2025-mig-1', 'btw2025', 'cat-btw2025-migration', 'Deutschland soll mehr Flüchtlinge aufnehmen.', '20', true, 1, NOW(), NOW()),
('the-btw2025-mig-2', 'btw2025', 'cat-btw2025-migration', 'Das Asylrecht soll strenger gefasst werden.', '20', true, 2, NOW(), NOW()),
('the-btw2025-mig-3', 'btw2025', 'cat-btw2025-migration', 'Familiennachzug für Geflüchtete soll eingeschränkt werden.', '40', true, 3, NOW(), NOW()),
('the-btw2025-mig-4', 'btw2025', 'cat-btw2025-migration', 'Integrationskurse sollen verpflichtend sein.', '40', true, 4, NOW(), NOW()),
('the-btw2025-mig-5', 'btw2025', 'cat-btw2025-migration', 'Aufenthaltstitel sollen an Deutschkenntnisse gekoppelt werden.', '60plus', true, 5, NOW(), NOW()),
('the-btw2025-mig-6', 'btw2025', 'cat-btw2025-migration', 'Abschiebungen bei straffälligen Geflüchteten sollen konsequenter erfolgen.', '60plus', true, 6, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- Demokratie und Verfassung (sensible Rubrik)
-- ============================================================
INSERT INTO thesis (id, election_id, category_id, statement, tier, weightable, sort_order, created_at, updated_at) VALUES
('the-btw2025-dem-1', 'btw2025', 'cat-btw2025-demokratie', 'Das Wahlalter soll auf 16 Jahre gesenkt werden.', '20', true, 1, NOW(), NOW()),
('the-btw2025-dem-2', 'btw2025', 'cat-btw2025-demokratie', 'Parteispenden sollen transparenter gemacht werden.', '20', true, 2, NOW(), NOW()),
('the-btw2025-dem-3', 'btw2025', 'cat-btw2025-demokratie', 'Volksentscheide auf Bundesebene sollen eingeführt werden.', '40', true, 3, NOW(), NOW()),
('the-btw2025-dem-4', 'btw2025', 'cat-btw2025-demokratie', 'Lobbyismus im Bundestag soll strenger reguliert werden.', '40', true, 4, NOW(), NOW()),
('the-btw2025-dem-5', 'btw2025', 'cat-btw2025-demokratie', 'Die Amtszeit des Kanzlers soll auf zwei Perioden begrenzt werden.', '60plus', true, 5, NOW(), NOW()),
('the-btw2025-dem-6', 'btw2025', 'cat-btw2025-demokratie', 'Abgeordnete sollen nicht in Aufsichtsräten von Unternehmen sitzen.', '60plus', true, 6, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- Verkehr und Infrastruktur
-- ============================================================
INSERT INTO thesis (id, election_id, category_id, statement, tier, weightable, sort_order, created_at, updated_at) VALUES
('the-btw2025-ver-1', 'btw2025', 'cat-btw2025-verkehr', 'Der öffentliche Personennahverkehr soll kostenlos sein.', '20', true, 1, NOW(), NOW()),
('the-btw2025-ver-2', 'btw2025', 'cat-btw2025-verkehr', 'Das Schienennetz soll stark ausgebaut werden.', '20', true, 2, NOW(), NOW()),
('the-btw2025-ver-3', 'btw2025', 'cat-btw2025-verkehr', 'Die Lkw-Maut soll auf alle Bundesstraßen ausgeweitet werden.', '40', true, 3, NOW(), NOW()),
('the-btw2025-ver-4', 'btw2025', 'cat-btw2025-verkehr', 'Radwege sollen flächendeckend ausgebaut werden.', '40', true, 4, NOW(), NOW()),
('the-btw2025-ver-5', 'btw2025', 'cat-btw2025-verkehr', 'Neue Autobahnstrecken sollen nicht mehr gebaut werden.', '60plus', true, 5, NOW(), NOW()),
('the-btw2025-ver-6', 'btw2025', 'cat-btw2025-verkehr', 'Die Lkw-Maut soll verdoppelt werden.', '60plus', true, 6, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- Digitales und Datenschutz
-- ============================================================
INSERT INTO thesis (id, election_id, category_id, statement, tier, weightable, sort_order, created_at, updated_at) VALUES
('the-btw2025-dig-1', 'btw2025', 'cat-btw2025-digital', 'Schnelles Internet soll flächendeckend staatlich gefördert werden.', '20', true, 1, NOW(), NOW()),
('the-btw2025-dig-2', 'btw2025', 'cat-btw2025-digital', 'Behördenleistungen sollen vollständig digital verfügbar sein.', '20', true, 2, NOW(), NOW()),
('the-btw2025-dig-3', 'btw2025', 'cat-btw2025-digital', 'Künstliche Intelligenz soll staatlich reguliert werden.', '40', true, 3, NOW(), NOW()),
('the-btw2025-dig-4', 'btw2025', 'cat-btw2025-digital', 'Ein Recht auf digitale Grundversorgung (Internet) soll gelten.', '40', true, 4, NOW(), NOW()),
('the-btw2025-dig-5', 'btw2025', 'cat-btw2025-digital', 'Gesichtserkennung an Bahnhöfen soll erlaubt sein.', '60plus', true, 5, NOW(), NOW()),
('the-btw2025-dig-6', 'btw2025', 'cat-btw2025-digital', 'Ende-zu-Ende-Verschlüsselung soll für Strafverfolgung durchbrochen werden dürfen.', '60plus', true, 6, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;
