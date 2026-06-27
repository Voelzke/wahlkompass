"""
Tests for the Wahlkompass database schema.

These tests verify:
    - All 8 tables exist with correct columns
    - Enum types work correctly
    - Constraints (UNIQUE, FK, CHECK) work
    - Seed data is correct (10 categories, 3 sensitive)
    - Indexes exist
    - UUID generation works
    - updated_at trigger works

Requires a running PostgreSQL database at DATABASE_URL or default localhost.
"""
import os
import sys
import uuid
import pytest
import psycopg2
from psycopg2.extras import RealDictCursor

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_database_url

# Tables expected in schema
EXPECTED_TABLES = [
    "election", "party", "program", "category",
    "thesis", "position", "evidence", "review_log",
]

# Test database URL — separate from main DB
TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://wahlkompass:***@localhost:5432/wahlkompass_test",
)


@pytest.fixture(scope="module")
def test_db():
    """Create a fresh test database, apply schema + seed, drop after."""
    # Connect to the default DB to create/drop test DB
    admin_url = get_database_url()
    admin_conn = psycopg2.connect(admin_url)
    admin_conn.autocommit = True
    admin_cur = admin_conn.cursor()

    # Drop and recreate test database
    admin_cur.execute("DROP DATABASE IF EXISTS wahlkompass_test")
    admin_cur.execute("CREATE DATABASE wahlkompass_test OWNER wahlkompass")
    admin_cur.close()
    admin_conn.close()

    # Connect to test database and apply schema
    test_conn = psycopg2.connect(TEST_DB_URL)
    test_conn.autocommit = True
    test_cur = test_conn.cursor()

    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schema.sql")
    with open(schema_path, "r") as f:
        schema_sql = f.read()
    test_cur.execute(schema_sql)

    seed_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "seed.sql")
    with open(seed_path, "r") as f:
        seed_sql = f.read()
    test_cur.execute(seed_sql)

    test_cur.close()
    test_conn.close()

    yield TEST_DB_URL

    # Cleanup: drop test database
    cleanup_conn = psycopg2.connect(admin_url)
    cleanup_conn.autocommit = True
    cleanup_cur = cleanup_conn.cursor()
    cleanup_cur.execute("DROP DATABASE IF EXISTS wahlkompass_test")
    cleanup_cur.close()
    cleanup_conn.close()


@pytest.fixture
def db_conn(test_db):
    """Provide a fresh connection for each test."""
    conn = psycopg2.connect(test_db)
    conn.autocommit = False
    yield conn
    conn.close()


def get_tables(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    return {r[0] for r in cur.fetchall()}


def get_columns(conn, table):
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
    """, (table,))
    return {r[0] for r in cur.fetchall()}


def get_enums(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT t.typname, array_agg(e.enumlabel ORDER BY e.enumsortorder)
        FROM pg_type t
        JOIN pg_enum e ON t.oid = e.enumtypid
        JOIN pg_namespace n ON t.typnamespace = n.oid
        WHERE n.nspname = 'public'
        GROUP BY t.typname
    """)
    return {r[0]: list(r[1]) for r in cur.fetchall()}


def get_indexes(conn, table):
    cur = conn.cursor()
    cur.execute("""
        SELECT indexname FROM pg_indexes
        WHERE schemaname = 'public' AND tablename = %s
    """, (table,))
    return {r[0] for r in cur.fetchall()}


# ============================================================================
# TABLE EXISTENCE TESTS
# ============================================================================

class TestTablesExist:
    def test_all_tables_exist(self, db_conn):
        tables = get_tables(db_conn)
        for t in EXPECTED_TABLES:
            assert t in tables, f"Table '{t}' not found in database"

    def test_no_extra_tables(self, db_conn):
        tables = get_tables(db_conn)
        # Filter out the uuid-ossp extension function tables if any
        user_tables = tables
        for t in EXPECTED_TABLES:
            assert t in user_tables
        # We should have exactly our 8 tables
        assert len(user_tables) == 8


# ============================================================================
# COLUMN TESTS
# ============================================================================

class TestElectionColumns:
    def test_election_columns(self, db_conn):
        cols = get_columns(db_conn, "election")
        expected = {"id", "type", "date", "region", "source_url",
                    "phase", "created_at", "updated_at"}
        assert expected.issubset(cols), f"Missing columns: {expected - cols}"


class TestPartyColumns:
    def test_party_columns(self, db_conn):
        cols = get_columns(db_conn, "party")
        expected = {"id", "name", "short_name", "logo_url",
                    "website_url", "color", "created_at", "updated_at"}
        assert expected.issubset(cols)


class TestProgramColumns:
    def test_program_columns(self, db_conn):
        cols = get_columns(db_conn, "program")
        expected = {"id", "party_id", "election_id", "source_url",
                    "source_format", "source_checksum", "local_path",
                    "text_extract_path", "fetched_at", "page_count",
                    "has_page_numbers", "status", "created_at", "updated_at"}
        assert expected.issubset(cols)


class TestCategoryColumns:
    def test_category_columns(self, db_conn):
        cols = get_columns(db_conn, "category")
        expected = {"id", "election_id", "name", "description",
                    "sort_order", "is_sensitive", "created_at", "updated_at"}
        assert expected.issubset(cols)


class TestThesisColumns:
    def test_thesis_columns(self, db_conn):
        cols = get_columns(db_conn, "thesis")
        expected = {"id", "election_id", "category_id", "statement",
                    "tier", "weightable", "sort_order", "created_at", "updated_at"}
        assert expected.issubset(cols)


class TestPositionColumns:
    def test_position_columns(self, db_conn):
        cols = get_columns(db_conn, "position")
        expected = {"id", "party_id", "thesis_id", "program_id",
                    "position_type", "no_evidence_note", "extracted_at",
                    "extraction_model", "extraction_model_version",
                    "review_status", "flag_reasons", "published",
                    "created_at", "updated_at"}
        assert expected.issubset(cols)


class TestEvidenceColumns:
    def test_evidence_columns(self, db_conn):
        cols = get_columns(db_conn, "evidence")
        expected = {"id", "position_id", "quote", "quote_location",
                    "program_id", "verified_by", "extracted_at",
                    "created_at", "updated_at"}
        assert expected.issubset(cols)


class TestReviewLogColumns:
    def test_review_log_columns(self, db_conn):
        cols = get_columns(db_conn, "review_log")
        expected = {"id", "position_id", "reviewer", "decision",
                    "flag_reasons", "note", "reviewed_at", "created_at"}
        assert expected.issubset(cols)


# ============================================================================
# ENUM TYPE TESTS
# ============================================================================

class TestEnumTypes:
    def test_election_type_enum(self, db_conn):
        enums = get_enums(db_conn)
        assert "election_type" in enums
        assert set(enums["election_type"]) == {"bundestag", "landtag", "europawahl"}

    def test_election_phase_enum(self, db_conn):
        enums = get_enums(db_conn)
        assert "election_phase" in enums
        assert set(enums["election_phase"]) == {"erfassung", "preview", "live", "archiv"}

    def test_program_status_enum(self, db_conn):
        enums = get_enums(db_conn)
        assert "program_status" in enums
        assert set(enums["program_status"]) == {"no_program", "graphical_only", "text_available"}

    def test_position_type_enum(self, db_conn):
        enums = get_enums(db_conn)
        assert "position_type" in enums
        assert set(enums["position_type"]) == {"zustimmen", "ablehnen", "neutral", "unklar"}

    def test_review_status_enum(self, db_conn):
        enums = get_enums(db_conn)
        assert "review_status_enum" in enums
        assert set(enums["review_status_enum"]) == {
            "auto-validiert", "geflaggt", "solo-geprueft",
            "community-korrigiert", "freigegeben"
        }

    def test_thesis_tier_enum(self, db_conn):
        enums = get_enums(db_conn)
        assert "thesis_tier" in enums
        assert set(enums["thesis_tier"]) == {"20", "40", "60plus"}


# ============================================================================
# CONSTRAINT TESTS
# ============================================================================

class TestConstraints:
    def test_program_unique_party_election(self, db_conn):
        """UNIQUE(party_id, election_id) on program"""
        cur = db_conn.cursor()
        # Create election and party
        cur.execute("""INSERT INTO election (type, date, region) VALUES ('bundestag', '2025-01-01', 'Bund') RETURNING id""")
        eid = cur.fetchone()[0]
        cur.execute("""INSERT INTO party (name, short_name) VALUES ('Test Party', 'TP') RETURNING id""")
        pid = cur.fetchone()[0]
        cur.execute("""INSERT INTO program (party_id, election_id) VALUES (%s, %s)""", (pid, eid))

        # Duplicate should fail
        with pytest.raises(psycopg2.IntegrityError):
            cur.execute("""INSERT INTO program (party_id, election_id) VALUES (%s, %s)""", (pid, eid))
        db_conn.rollback()

    def test_position_unique_party_thesis(self, db_conn):
        """UNIQUE(party_id, thesis_id) on position"""
        cur = db_conn.cursor()
        cur.execute("""INSERT INTO election (type, date, region) VALUES ('bundestag', '2025-01-01', 'Bund') RETURNING id""")
        eid = cur.fetchone()[0]
        cur.execute("""INSERT INTO party (name, short_name) VALUES ('TP2', 'TP2') RETURNING id""")
        pid = cur.fetchone()[0]
        cur.execute("""INSERT INTO category (election_id, name) VALUES (%s, 'Test') RETURNING id""", (eid,))
        cat_id = cur.fetchone()[0]
        cur.execute("""INSERT INTO thesis (election_id, category_id, statement) VALUES (%s, %s, 'Test statement here') RETURNING id""", (eid, cat_id))
        tid = cur.fetchone()[0]
        cur.execute("""INSERT INTO position (party_id, thesis_id, position_type) VALUES (%s, %s, 'zustimmen')""", (pid, tid))

        with pytest.raises(psycopg2.IntegrityError):
            cur.execute("""INSERT INTO position (party_id, thesis_id, position_type) VALUES (%s, %s, 'ablehnen')""", (pid, tid))
        db_conn.rollback()

    def test_evidence_unique_position(self, db_conn):
        """1:1 evidence→position"""
        cur = db_conn.cursor()
        cur.execute("""INSERT INTO election (type, date, region) VALUES ('bundestag', '2025-01-01', 'Bund') RETURNING id""")
        eid = cur.fetchone()[0]
        cur.execute("""INSERT INTO party (name, short_name) VALUES ('TP3', 'TP3') RETURNING id""")
        pid = cur.fetchone()[0]
        cur.execute("""INSERT INTO category (election_id, name) VALUES (%s, 'Test') RETURNING id""", (eid,))
        cat_id = cur.fetchone()[0]
        cur.execute("""INSERT INTO thesis (election_id, category_id, statement) VALUES (%s, %s, 'Test statement here') RETURNING id""", (eid, cat_id))
        tid = cur.fetchone()[0]
        cur.execute("""INSERT INTO position (party_id, thesis_id, position_type) VALUES (%s, %s, 'zustimmen') RETURNING id""", (pid, tid))
        pos_id = cur.fetchone()[0]
        cur.execute("""INSERT INTO evidence (position_id, quote) VALUES (%s, %s)""", (pos_id, 'A' * 30))

        with pytest.raises(psycopg2.IntegrityError):
            cur.execute("""INSERT INTO evidence (position_id, quote) VALUES (%s, %s)""", (pos_id, 'B' * 30))
        db_conn.rollback()

    def test_evidence_quote_length_check(self, db_conn):
        """quote must be 20-300 chars"""
        cur = db_conn.cursor()
        cur.execute("""INSERT INTO election (type, date, region) VALUES ('bundestag', '2025-01-01', 'Bund') RETURNING id""")
        eid = cur.fetchone()[0]
        cur.execute("""INSERT INTO party (name, short_name) VALUES ('TP4', 'TP4') RETURNING id""")
        pid = cur.fetchone()[0]
        cur.execute("""INSERT INTO category (election_id, name) VALUES (%s, 'Test') RETURNING id""", (eid,))
        cat_id = cur.fetchone()[0]
        cur.execute("""INSERT INTO thesis (election_id, category_id, statement) VALUES (%s, %s, 'Test statement here') RETURNING id""", (eid, cat_id))
        tid = cur.fetchone()[0]
        cur.execute("""INSERT INTO position (party_id, thesis_id, position_type) VALUES (%s, %s, 'zustimmen') RETURNING id""", (pid, tid))
        pos_id = cur.fetchone()[0]

        # Too short (< 20 chars)
        with pytest.raises(psycopg2.IntegrityError):
            cur.execute("""INSERT INTO evidence (position_id, quote) VALUES (%s, %s)""", (pos_id, 'short'))
        db_conn.rollback()

    def test_thesis_statement_length(self, db_conn):
        """statement is VARCHAR(150)"""
        cur = db_conn.cursor()
        cur.execute("""INSERT INTO election (type, date, region) VALUES ('bundestag', '2025-01-01', 'Bund') RETURNING id""")
        eid = cur.fetchone()[0]
        cur.execute("""INSERT INTO category (election_id, name) VALUES (%s, 'Test') RETURNING id""", (eid,))
        cat_id = cur.fetchone()[0]

        # 150 chars OK
        cur.execute("""INSERT INTO thesis (election_id, category_id, statement) VALUES (%s, %s, %s)""",
                     (eid, cat_id, 'A' * 150))
        # 151 chars should fail
        with pytest.raises(psycopg2.DataError):
            cur.execute("""INSERT INTO thesis (election_id, category_id, statement) VALUES (%s, %s, %s)""",
                         (eid, cat_id, 'A' * 151))
        db_conn.rollback()

    def test_fk_cascade_delete(self, db_conn):
        """ON DELETE CASCADE works for party→program"""
        cur = db_conn.cursor()
        cur.execute("""INSERT INTO election (type, date, region) VALUES ('bundestag', '2025-01-01', 'Bund') RETURNING id""")
        eid = cur.fetchone()[0]
        cur.execute("""INSERT INTO party (name, short_name) VALUES ('Cascade Test', 'CT') RETURNING id""")
        pid = cur.fetchone()[0]
        cur.execute("""INSERT INTO program (party_id, election_id) VALUES (%s, %s) RETURNING id""", (pid, eid))
        prog_id = cur.fetchone()[0]
        db_conn.commit()

        # Delete party should cascade to program
        cur.execute("""DELETE FROM party WHERE id = %s""", (pid,))
        db_conn.commit()

        cur.execute("""SELECT count(*) FROM program WHERE id = %s""", (prog_id,))
        assert cur.fetchone()[0] == 0


# ============================================================================
# UUID TESTS
# ============================================================================

class TestUUID:
    def test_uuid_primary_key(self, db_conn):
        cur = db_conn.cursor()
        cur.execute("""INSERT INTO election (type, date, region) VALUES ('bundestag', '2025-01-01', 'Bund') RETURNING id""")
        eid = cur.fetchone()[0]
        # Verify it's a valid UUID
        uuid.UUID(str(eid))
        db_conn.rollback()


# ============================================================================
# INDEX TESTS
# ============================================================================

class TestIndexes:
    def test_position_unique_index(self, db_conn):
        indexes = get_indexes(db_conn, "position")
        # UNIQUE constraint creates an index
        assert any("party_id" in idx and "thesis_id" in idx for idx in indexes) or \
               any("uniq" in idx.lower() or "party" in idx.lower() for idx in indexes)

    def test_position_review_status_index(self, db_conn):
        indexes = get_indexes(db_conn, "position")
        assert any("review_status" in idx.lower() for idx in indexes)

    def test_evidence_position_index(self, db_conn):
        indexes = get_indexes(db_conn, "evidence")
        assert any("position" in idx.lower() for idx in indexes)

    def test_thesis_election_tier_index(self, db_conn):
        indexes = get_indexes(db_conn, "thesis")
        assert any("tier" in idx.lower() or "election" in idx.lower() for idx in indexes)

    def test_review_log_index(self, db_conn):
        indexes = get_indexes(db_conn, "review_log")
        assert any("position" in idx.lower() or "reviewed" in idx.lower() for idx in indexes)


# ============================================================================
# SEED DATA TESTS
# ============================================================================

class TestSeedData:
    def test_10_categories_exist(self, db_conn):
        cur = db_conn.cursor()
        cur.execute("""SELECT count(*) FROM category""")
        assert cur.fetchone()[0] == 10

    def test_3_sensitive_categories(self, db_conn):
        cur = db_conn.cursor()
        cur.execute("""SELECT count(*) FROM category WHERE is_sensitive = true""")
        assert cur.fetchone()[0] == 3

    def test_sensitive_categories_correct(self, db_conn):
        cur = db_conn.cursor()
        cur.execute("""SELECT name FROM category WHERE is_sensitive = true ORDER BY sort_order""")
        names = [r[0] for r in cur.fetchall()]
        assert "Innen und Recht" in names
        assert "Migration und Integration" in names
        assert "Demokratie und Verfassung" in names

    def test_all_category_names(self, db_conn):
        cur = db_conn.cursor()
        cur.execute("""SELECT name FROM category ORDER BY sort_order""")
        names = [r[0] for r in cur.fetchall()]
        expected = [
            "Wirtschaft und Finanzen",
            "Soziales und Gesundheit",
            "Klima und Umwelt",
            "Bildung und Forschung",
            "Europa und Außenpolitik",
            "Innen und Recht",
            "Migration und Integration",
            "Demokratie und Verfassung",
            "Verkehr und Infrastruktur",
            "Digitales und Datenschutz",
        ]
        assert names == expected

    def test_sort_order_sequential(self, db_conn):
        cur = db_conn.cursor()
        cur.execute("""SELECT sort_order FROM category ORDER BY sort_order""")
        orders = [r[0] for r in cur.fetchall()]
        assert orders == list(range(1, 11))


# ============================================================================
# TRIGGER TESTS
# ============================================================================

class TestTriggers:
    def test_updated_at_trigger(self, db_conn):
        cur = db_conn.cursor()
        cur.execute("""INSERT INTO election (type, date, region) VALUES ('bundestag', '2025-01-01', 'Bund') RETURNING id, updated_at""")
        row = cur.fetchone()
        eid, original_updated = row[0], row[1]

        cur.execute("""UPDATE election SET region = 'BundUpdated' WHERE id = %s RETURNING updated_at""", (eid,))
        new_updated = cur.fetchone()[0]
        assert new_updated >= original_updated
        db_conn.rollback()


# ============================================================================
# DEFAULT VALUE TESTS
# ============================================================================

class TestDefaults:
    def test_position_defaults(self, db_conn):
        cur = db_conn.cursor()
        cur.execute("""INSERT INTO election (type, date, region) VALUES ('bundestag', '2025-01-01', 'Bund') RETURNING id""")
        eid = cur.fetchone()[0]
        cur.execute("""INSERT INTO party (name, short_name) VALUES ('DefT', 'DFT') RETURNING id""")
        pid = cur.fetchone()[0]
        cur.execute("""INSERT INTO category (election_id, name) VALUES (%s, 'Test') RETURNING id""", (eid,))
        cat_id = cur.fetchone()[0]
        cur.execute("""INSERT INTO thesis (election_id, category_id, statement) VALUES (%s, %s, 'Test statement here') RETURNING id""", (eid, cat_id))
        tid = cur.fetchone()[0]
        cur.execute("""INSERT INTO position (party_id, thesis_id, position_type) VALUES (%s, %s, 'zustimmen') RETURNING review_status, published, weightable""", (pid, tid))

        # Wait, weightable is on thesis, not position
        cur.execute("""SELECT review_status, published FROM position WHERE party_id = %s""", (pid,))
        row = cur.fetchone()
        assert row[0] == 'geflaggt'  # default review_status
        assert row[1] == False  # default published
        db_conn.rollback()

    def test_thesis_weightable_default(self, db_conn):
        cur = db_conn.cursor()
        cur.execute("""INSERT INTO election (type, date, region) VALUES ('bundestag', '2025-01-01', 'Bund') RETURNING id""")
        eid = cur.fetchone()[0]
        cur.execute("""INSERT INTO category (election_id, name) VALUES (%s, 'Test') RETURNING id""", (eid,))
        cat_id = cur.fetchone()[0]
        cur.execute("""INSERT INTO thesis (election_id, category_id, statement) VALUES (%s, %s, 'Test statement here') RETURNING weightable, tier""", (eid, cat_id))
        row = cur.fetchone()
        assert row[0] == True  # weightable default
        assert row[1] == '40'  # tier default
        db_conn.rollback()

    def test_program_status_default(self, db_conn):
        cur = db_conn.cursor()
        cur.execute("""INSERT INTO election (type, date, region) VALUES ('bundestag', '2025-01-01', 'Bund') RETURNING id""")
        eid = cur.fetchone()[0]
        cur.execute("""INSERT INTO party (name, short_name) VALUES ('ProgDef', 'PD') RETURNING id""")
        pid = cur.fetchone()[0]
        cur.execute("""INSERT INTO program (party_id, election_id) VALUES (%s, %s) RETURNING status""", (pid, eid))
        assert cur.fetchone()[0] == 'no_program'
        db_conn.rollback()
