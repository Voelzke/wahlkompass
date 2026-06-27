-- Seed: BTW 2025 Wahl
-- Erstellt die BTW 2025 Saison mit Standard-Rubriken

INSERT INTO election (id, type, date, region, source_url, phase, created_at, updated_at)
VALUES (
    'btw2025',
    'bundestag',
    '2025-02-23',
    'Bund',
    'https://www.bundeswahlleiter.de/bundestagswahlen/2025/unterlagen/landeslisten.html',
    'erfassung',
    NOW(),
    NOW()
)
ON CONFLICT (id) DO NOTHING;

-- Standard-Rubriken (10 Kategorien)
INSERT INTO category (id, election_id, name, description, sort_order, is_sensitive, created_at, updated_at)
VALUES
    ('cat-btw2025-wirtschaft', 'btw2025', 'Wirtschaft und Finanzen', 'Wirtschaftspolitik, Haushalt, Steuern, Schulden', 1, false, NOW(), NOW()),
    ('cat-btw2025-soziales', 'btw2025', 'Soziales und Gesundheit', 'Renten, Krankenversicherung, Pflege, Gesundheitsversorgung', 2, false, NOW(), NOW()),
    ('cat-btw2025-klima', 'btw2025', 'Klima und Umwelt', 'Klimaschutz, Energiepolitik, Naturschutz, CO2-Reduktion', 3, false, NOW(), NOW()),
    ('cat-btw2025-bildung', 'btw2025', 'Bildung und Forschung', 'Schulpolitik, Hochschulen, Forschungsförderung, Bildungsgerechtigkeit', 4, false, NOW(), NOW()),
    ('cat-btw2025-europa', 'btw2025', 'Europa und Außenpolitik', 'EU-Integration, Außenhandel, Entwicklungshilfe, Sicherheit', 5, false, NOW(), NOW()),
    ('cat-btw2025-innen', 'btw2025', 'Innen und Recht', 'Innere Sicherheit, Justiz, Verfassungsschutz, Polizei', 6, true, NOW(), NOW()),
    ('cat-btw2025-migration', 'btw2025', 'Migration und Integration', 'Einwanderungspolitik, Asyl, Integration, Flucht', 7, true, NOW(), NOW()),
    ('cat-btw2025-demokratie', 'btw2025', 'Demokratie und Verfassung', 'Demokratiequalität, Wahlrecht, Parteienfinanzierung, Bürgerrechte', 8, true, NOW(), NOW()),
    ('cat-btw2025-verkehr', 'btw2025', 'Verkehr und Infrastruktur', 'Mobilität, öffentlicher Nahverkehr, Digitalinfrastruktur', 9, false, NOW(), NOW()),
    ('cat-btw2025-digital', 'btw2025', 'Digitales und Datenschutz', 'Digitalisierung, Datenschutz, KI-Regulierung, Netzpolitik', 10, false, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;
