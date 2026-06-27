-- Seed data: 10 standard categories for a new election season
-- is_sensitive=true for Migration, Demokratie, Innen
-- These are inserted per-election via init_season.py, but this file
-- serves as both reference data and a standalone seed for testing.

-- NOTE: This file expects an election row with id = '00000000-0000-0000-0000-000000000001'
-- to exist. For production use, run init_season.py which creates the election
-- and inserts these categories with the correct election_id.

-- For standalone testing, create a test election first:
INSERT INTO election (id, type, date, region, phase)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'bundestag',
    '2025-02-23',
    'Bund',
    'archiv'
)
ON CONFLICT (id) DO NOTHING;

-- 10 standard categories (sorted by sort_order)
INSERT INTO category (election_id, name, description, sort_order, is_sensitive)
VALUES
    ('00000000-0000-0000-0000-000000000001', 'Wirtschaft und Finanzen',
     'Steuer-, Haushalts- und Wirtschaftspolitik, Arbeitsmarkt, öffentliche Finanzen',
     1, false),
    ('00000000-0000-0000-0000-000000000001', 'Soziales und Gesundheit',
     'Renten-, Gesundheits- und Sozialpolitik, Pflege, Arbeitslosenschutz',
     2, false),
    ('00000000-0000-0000-0000-000000000001', 'Klima und Umwelt',
     'Klimaschutz, Energiepolitik, Umweltschutz, erneuerbare Energien',
     3, false),
    ('00000000-0000-0000-0000-000000000001', 'Bildung und Forschung',
     'Bildungspolitik, Schulen, Hochschulen, Forschungsförderung, Wissenschaft',
     4, false),
    ('00000000-0000-0000-0000-000000000001', 'Europa und Außenpolitik',
     'Europäische Union, Außen- und Sicherheitspolitik, internationale Zusammenarbeit',
     5, false),
    ('00000000-0000-0000-0000-000000000001', 'Innen und Recht',
     'Innere Sicherheit, Justiz, Verbraucherschutz, Datenschutzgrundlagen',
     6, true),
    ('00000000-0000-0000-0000-000000000001', 'Migration und Integration',
     'Migrationspolitik, Asyl, Integration, Einwanderungsgesetze',
     7, true),
    ('00000000-0000-0000-0000-000000000001', 'Demokratie und Verfassung',
     'Verfassungsrecht, Demokratieförderung, Wahlsystem, politische Teilhabe',
     8, true),
    ('00000000-0000-0000-0000-000000000001', 'Verkehr und Infrastruktur',
     'Verkehrspolitik, Mobilität, digitale und physische Infrastruktur',
     9, false),
    ('00000000-0000-0000-0000-000000000001', 'Digitales und Datenschutz',
     'Digitalisierung, KI-Regulierung, IT-Sicherheit, digitale Grundrechte',
     10, false)
ON CONFLICT DO NOTHING;
