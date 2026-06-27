-- Wahlkompass Database Schema
-- PostgreSQL 16+
-- All tables use UUID primary keys via uuid-ossp

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- ENUM TYPES
-- ============================================================================

CREATE TYPE election_type AS ENUM ('bundestag', 'landtag', 'europawahl');
CREATE TYPE election_phase AS ENUM ('erfassung', 'preview', 'live', 'archiv');
CREATE TYPE program_source_format AS ENUM ('pdf', 'html');
CREATE TYPE program_status AS ENUM ('no_program', 'graphical_only', 'text_available');
CREATE TYPE thesis_tier AS ENUM ('20', '40', '60plus');
CREATE TYPE position_type AS ENUM ('zustimmen', 'ablehnen', 'neutral', 'unklar');
CREATE TYPE review_status_enum AS ENUM ('auto-validiert', 'geflaggt', 'solo-geprueft', 'community-korrigiert', 'freigegeben');
CREATE TYPE evidence_verified_by AS ENUM ('auto', 'solo', 'community');
CREATE TYPE reviewer_type AS ENUM ('auto', 'solo', 'community');
CREATE TYPE review_decision AS ENUM ('freigeben', 'korrigieren', 'unklar', 're-extract', 'flag');

-- ============================================================================
-- TABLES
-- ============================================================================

-- 1. election ----------------------------------------------------------------
CREATE TABLE election (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type        election_type NOT NULL,
    date        DATE NOT NULL,
    region      VARCHAR(255) NOT NULL,
    source_url  TEXT,
    phase       election_phase NOT NULL DEFAULT 'erfassung',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. party -------------------------------------------------------------------
CREATE TABLE party (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name         VARCHAR(255) NOT NULL,
    short_name   VARCHAR(20) NOT NULL,
    logo_url     TEXT,
    website_url  TEXT,
    color        VARCHAR(7),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. program -----------------------------------------------------------------
CREATE TABLE program (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    party_id            UUID NOT NULL REFERENCES party(id) ON DELETE CASCADE,
    election_id         UUID NOT NULL REFERENCES election(id) ON DELETE CASCADE,
    source_url          TEXT,
    source_format       program_source_format,
    source_checksum     VARCHAR(64),
    local_path          TEXT,
    text_extract_path   TEXT,
    fetched_at          TIMESTAMPTZ,
    page_count          INT,
    has_page_numbers    BOOLEAN,
    status              program_status NOT NULL DEFAULT 'no_program',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(party_id, election_id)
);

-- 4. category ----------------------------------------------------------------
CREATE TABLE category (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    election_id UUID NOT NULL REFERENCES election(id) ON DELETE CASCADE,
    name        VARCHAR(40) NOT NULL,
    description TEXT,
    sort_order  INT NOT NULL DEFAULT 0,
    is_sensitive BOOLEAN NOT NULL DEFAULT false,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 5. thesis ------------------------------------------------------------------
CREATE TABLE thesis (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    election_id  UUID NOT NULL REFERENCES election(id) ON DELETE CASCADE,
    category_id  UUID NOT NULL REFERENCES category(id) ON DELETE CASCADE,
    statement   VARCHAR(150) NOT NULL,
    tier         thesis_tier NOT NULL DEFAULT '40',
    weightable   BOOLEAN NOT NULL DEFAULT true,
    sort_order   INT NOT NULL DEFAULT 0,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 6. position ----------------------------------------------------------------
CREATE TABLE position (
    id                       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    party_id                 UUID NOT NULL REFERENCES party(id) ON DELETE CASCADE,
    thesis_id                UUID NOT NULL REFERENCES thesis(id) ON DELETE CASCADE,
    program_id               UUID REFERENCES program(id) ON DELETE SET NULL,
    position_type           position_type NOT NULL,
    no_evidence_note         TEXT,
    extracted_at             TIMESTAMPTZ,
    extraction_model         VARCHAR(255),
    extraction_model_version VARCHAR(64),
    review_status            review_status_enum NOT NULL DEFAULT 'geflaggt',
    flag_reasons             TEXT[],
    published               BOOLEAN NOT NULL DEFAULT false,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(party_id, thesis_id)
);

-- 7. evidence ----------------------------------------------------------------
CREATE TABLE evidence (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    position_id  UUID NOT NULL REFERENCES position(id) ON DELETE CASCADE,
    quote        TEXT NOT NULL CHECK (char_length(quote) BETWEEN 20 AND 300),
    quote_location JSONB,
    program_id   UUID REFERENCES program(id) ON DELETE SET NULL,
    verified_by  evidence_verified_by NOT NULL DEFAULT 'auto',
    extracted_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(position_id)  -- 1:1 with position
);

-- 8. review_log --------------------------------------------------------------
CREATE TABLE review_log (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    position_id  UUID NOT NULL REFERENCES position(id) ON DELETE CASCADE,
    reviewer     reviewer_type NOT NULL,
    decision     review_decision NOT NULL,
    flag_reasons TEXT[],
    note         TEXT,
    reviewed_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- INDEXES
-- ============================================================================
CREATE INDEX idx_position_party_thesis ON position(party_id, thesis_id);  -- also UNIQUE above
CREATE INDEX idx_position_thesis_review ON position(thesis_id, review_status);
CREATE INDEX idx_position_review_status ON position(review_status);
CREATE INDEX idx_evidence_position ON evidence(position_id);
CREATE INDEX idx_thesis_election_tier ON thesis(election_id, tier);
CREATE INDEX idx_program_party_election ON program(party_id, election_id);  -- also UNIQUE above
CREATE INDEX idx_review_log_position_reviewed ON review_log(position_id, reviewed_at);

-- ============================================================================
-- TRIGGER: updated_at auto-update
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_election_updated_at BEFORE UPDATE ON election FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_party_updated_at BEFORE UPDATE ON party FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_program_updated_at BEFORE UPDATE ON program FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_category_updated_at BEFORE UPDATE ON category FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_thesis_updated_at BEFORE UPDATE ON thesis FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_position_updated_at BEFORE UPDATE ON position FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_evidence_updated_at BEFORE UPDATE ON evidence FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
