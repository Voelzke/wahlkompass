-- Seed: Parteien BTW 2025
-- Die wichtigsten antretenden Parteien mit Farben und Webseiten
-- Kleinere Parteien als no_program

INSERT INTO party (id, name, short_name, logo_url, website_url, color, created_at, updated_at) VALUES
('party-spd', 'Sozialdemokratische Partei Deutschlands', 'SPD', NULL, 'https://www.spd.de', '#E3000F', NOW(), NOW()),
('party-cdu', 'Christlich Demokratische Union Deutschlands', 'CDU', NULL, 'https://www.cdu.de', '#000000', NOW(), NOW()),
('party-csu', 'Christlich-Soziale Union in Bayern', 'CSU', NULL, 'https://www.csu.de', '#0080C8', NOW(), NOW()),
('party-gruene', 'Bündnis 90/Die Grünen', 'Grüne', NULL, 'https://www.gruene.de', '#46A046', NOW(), NOW()),
('party-fdp', 'Freie Demokratische Partei', 'FDP', NULL, 'https://www.fdp.de', '#FFED00', NOW(), NOW()),
('party-afd', 'Alternative für Deutschland', 'AfD', NULL, 'https://www.afd.de', '#009EE0', NOW(), NOW()),
('party-linke', 'Die Linke', 'Linke', NULL, 'https://www.die-linke.de', '#BE3075', NOW(), NOW()),
('party-bsw', 'Bündnis Sahra Wagenknecht', 'BSW', NULL, 'https://www.bsw-vg.de', '#8E2DE2', NOW(), NOW()),
('party-fw', 'Freie Wähler', 'FW', NULL, 'https://www.freie-waehler.de', '#FF8C00', NOW(), NOW()),
('party-partei', 'Die PARTEI', 'PARTEI', NULL, 'https://www.die-partei.de', '#722F37', NOW(), NOW()),
('party-tierschutz', 'Partei Mensch Umwelt Tierschutz', 'Tiersch.', NULL, 'https://www.tierschutzpartei.de', '#7BB62E', NOW(), NOW()),
('party-npd', 'Die Heimat (NPD)', 'Heimat', NULL, 'https://www.dieheimat.de', '#8B0000', NOW(), NOW()),
('party-diebasis', 'dieBasis', 'dieBasis', NULL, 'https://www.diebasis-partei.de', '#4B0082', NOW(), NOW()),
('party-grauen', 'Die Grauen – Graue Panther', 'Graue', NULL, 'https://www.grauepanther.de', '#999999', NOW(), NOW()),
('party-violetten', 'Die Violetten', 'Violette', NULL, 'https://www.die-violetten.de', '#8B00FF', NOW(), NOW()),
('party-humanisten', 'Partei der Humanisten', 'PdH', NULL, 'https://www.parteiderhumanisten.de', '#FF6600', NOW(), NOW()),
('party-mlpd', 'Marxistisch-Leninistische Partei Deutschlands', 'MLPD', NULL, 'https://www.mlpd.de', '#FF0000', NOW(), NOW()),
('party-oedp', 'Ökologisch-Demokratische Partei', 'ÖDP', NULL, 'https://www.oedp.de', '#FFA500', NOW(), NOW()),
('party-bueso', 'Bürgerrechtsbewegung Solidarität', 'BüSo', NULL, 'https://www.bueso.de', '#00008B', NOW(), NOW()),
('party-buendnisc', 'Bündnis C – Christen für Deutschland', 'Bündnis C', NULL, 'https://www.buendnis-c.de', '#0066CC', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- Program entries for BTW 2025 (status = no_program until URLs verified)
INSERT INTO program (id, party_id, election_id, source_url, source_format, source_checksum, local_path, text_extract_path, fetched_at, page_count, has_page_numbers, status, created_at, updated_at)
SELECT 'prog-' || p.id || '-btw2025', p.id, 'btw2025',
    COALESCE(p.website_url || '/wahlprogramm', ''),
    'pdf',
    '',
    '',
    '',
    NULL,
    NULL,
    false,
    'no_program',
    NOW(),
    NOW()
FROM party p
ON CONFLICT (party_id, election_id) DO NOTHING;
