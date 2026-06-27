-- Schema für das Review-Modul (AP5)
-- ------------------------------------------------------------------
-- Diese Datei definiert die Tabellen, die das Review-CLI (review/cli.py)
-- erwartet. Sie ist als Ergänzung zum Hauptschema (packages/db/schema.sql)
-- gedacht und verwendet CREATE TABLE IF NOT EXISTS, sodass sie idempotent
-- ist und problemlos zusammen mit dem Hauptschema laufen kann.
--
-- Alle Tabellen verwenden TEXT-IDs (Slugs wie 'btw2025'), um menschenlesbare
-- Referenzen zu ermöglichen. Enums werden als TEXT mit CHECK-Constraints
-- abgebildet, damit das Schema portabel bleibt.
-- ------------------------------------------------------------------

-- Wahlen / Saisons (bereits im Hauptschema vorhanden — hier nur zur
-- Vollständigkeit, falls isoliert mit review/schema_review.sql gestartet wird)
CREATE TABLE IF NOT EXISTS election (
    id          TEXT PRIMARY KEY,
    type        TEXT NOT NULL,
    date        DATE NOT NULL,
    region      TEXT NOT NULL,
    source_url  TEXT,
    phase       TEXT NOT NULL DEFAULT 'erfassung',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Rubriken / Kategorien
CREATE TABLE IF NOT EXISTS category (
    id           TEXT PRIMARY KEY,
    election_id  TEXT NOT NULL REFERENCES election(id) ON DELETE CASCADE,
    name         TEXT NOT NULL,
    description  TEXT,
    sort_order   INTEGER NOT NULL DEFAULT 0,
    is_sensitive BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Parteien (pro Wahl)
CREATE TABLE IF NOT EXISTS party (
    id           TEXT PRIMARY KEY,
    election_id  TEXT NOT NULL REFERENCES election(id) ON DELETE CASCADE,
    name         TEXT NOT NULL,
    short_name   TEXT,
    is_admitted  BOOLEAN NOT NULL DEFAULT TRUE,
    source_url   TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Thesen (Aussagen, zu denen Parteien positioniert werden)
CREATE TABLE IF NOT EXISTS thesis (
    id           TEXT PRIMARY KEY,
    election_id  TEXT NOT NULL REFERENCES election(id) ON DELETE CASCADE,
    category_id  TEXT REFERENCES category(id) ON DELETE SET NULL,
    statement    TEXT NOT NULL,
    sort_order   INTEGER NOT NULL DEFAULT 0,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Parteipositionen
-- position_type: zustimmen | ablehnen | neutral | unklar
-- review_status: pending | solo-geprueft | re-extraction | community-geprueft
-- flags: JSONB-Array von Flag-Gründen, z.B. ["missing_evidence","low_confidence"]
--        Mögliche Flags:
--          missing_evidence     — kein Beleg oder Beleg zu kurz
--          low_confidence       — KI-Extraktion mit niedriger Konfidenz
--          short_quote          — Zitat < 20 Zeichen
--          ambiguous_position   — Positionstyp nicht eindeutig
--          source_mismatch      — Quelle passt nicht zur These
--          unresolved_quote     — Zitat in Quelle nicht auffindbar
CREATE TABLE IF NOT EXISTS position (
    id            TEXT PRIMARY KEY,
    election_id   TEXT NOT NULL REFERENCES election(id) ON DELETE CASCADE,
    party_id      TEXT NOT NULL REFERENCES party(id) ON DELETE CASCADE,
    thesis_id     TEXT NOT NULL REFERENCES thesis(id) ON DELETE CASCADE,
    position_type TEXT NOT NULL DEFAULT 'unklar'
                    CHECK (position_type IN ('zustimmen','ablehnen','neutral','unklar')),
    review_status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (review_status IN ('pending','solo-geprueft','re-extraction','community-geprueft')),
    flags         JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence    REAL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_position_election ON position(election_id);
CREATE INDEX IF NOT EXISTS idx_position_party ON position(party_id);
CREATE INDEX IF NOT EXISTS idx_position_flags ON position
    USING gin (flags);

-- Belege (Zitat + Quelle) pro Position
CREATE TABLE IF NOT EXISTS beleg (
    id          TEXT PRIMARY KEY,
    position_id TEXT NOT NULL REFERENCES position(id) ON DELETE CASCADE,
    quote       TEXT NOT NULL,
    source      TEXT NOT NULL,
    page        TEXT,
    url         TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_beleg_position ON beleg(position_id);

-- Review-Log: jede Entscheidung wird protokolliert (Audit-Trail)
CREATE TABLE IF NOT EXISTS review_log (
    id          TEXT PRIMARY KEY,
    position_id TEXT NOT NULL REFERENCES position(id) ON DELETE CASCADE,
    action      TEXT NOT NULL,
    reviewer    TEXT NOT NULL,
    note        TEXT,
    before_state JSONB,
    after_state  JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_review_log_position ON review_log(position_id);
CREATE INDEX IF NOT EXISTS idx_review_log_created ON review_log(created_at);
