"""Tests für das Review-CLI (AP5).

Alle Tests verwenden ``unittest.mock`` — es wird keine echte Datenbank
benötigt. Getestet werden:

* ReviewDB-Logik (Validierung, Delegation an Mock-Connections)
* CLI-Befehle via ``click.testing.CliRunner``
* Audit-Log-Schreibung
* Batch-Aktion
* Fehlerbehandlung (fehlende DATABASE_URL, ungültige Eingaben)

Ausführung::

    pytest review/tests/ -v
"""

from __future__ import annotations

import json
import os
from unittest import mock

import pytest
from click.testing import CliRunner

from review.cli import cli
from review.db import (
    KNOWN_FLAGS,
    VALID_POSITION_TYPES,
    VALID_REVIEW_STATUSES,
    FlaggedPosition,
    ReviewDB,
)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture
def env_db(monkeypatch):
    """Setzt eine Dummy-DATABASE_URL."""
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:pass@localhost:5432/wahlkompass",
    )
    monkeypatch.delenv("REVIEWER", raising=False)


@pytest.fixture
def runner():
    return CliRunner()


def _make_position(**overrides):
    """Erzeugt eine FlaggedPosition mit Standardwerten."""
    defaults = dict(
        id="pos-1",
        party_name="SPD",
        thesis_statement="Deutschland soll ein CO2-Budget festlegen.",
        position_type="zustimmen",
        review_status="pending",
        flags=["missing_evidence"],
        beleg_quote="Ein langes Zitat aus dem Programm.",
        beleg_source="Bundestagswahlprogramm 2025",
        beleg_page="42",
        beleg_url="https://example.org/programm.pdf",
    )
    defaults.update(overrides)
    return FlaggedPosition(**defaults)


# --------------------------------------------------------------------------- #
# FlaggedPosition.from_row
# --------------------------------------------------------------------------- #


class TestFlaggedPosition:
    def test_from_row_parses_json_string_flags(self):
        row = {
            "id": "pos-1",
            "party_name": "SPD",
            "thesis_statement": "These A",
            "position_type": "zustimmen",
            "review_status": "pending",
            "flags": '["missing_evidence", "low_confidence"]',
            "beleg_quote": None,
            "beleg_source": None,
            "beleg_page": None,
            "beleg_url": None,
        }
        pos = FlaggedPosition.from_row(row)
        assert pos.flags == ["missing_evidence", "low_confidence"]

    def test_from_row_handles_none_flags(self):
        row = {
            "id": "pos-1",
            "party_name": "SPD",
            "thesis_statement": "These A",
            "position_type": "zustimmen",
            "review_status": "pending",
            "flags": None,
            "beleg_quote": None,
            "beleg_source": None,
            "beleg_page": None,
            "beleg_url": None,
        }
        pos = FlaggedPosition.from_row(row)
        assert pos.flags == []

    def test_from_row_handles_invalid_json_flags(self):
        row = {
            "id": "pos-1",
            "party_name": "SPD",
            "thesis_statement": "These A",
            "position_type": "zustimmen",
            "review_status": "pending",
            "flags": "not-json",
            "beleg_quote": None,
            "beleg_source": None,
            "beleg_page": None,
            "beleg_url": None,
        }
        pos = FlaggedPosition.from_row(row)
        assert pos.flags == []

    def test_from_row_handles_list_flags(self):
        row = {
            "id": "pos-1",
            "party_name": "SPD",
            "thesis_statement": "These A",
            "position_type": "zustimmen",
            "review_status": "pending",
            "flags": ["short_quote"],
            "beleg_quote": "q",
            "beleg_source": "s",
            "beleg_page": None,
            "beleg_url": None,
        }
        pos = FlaggedPosition.from_row(row)
        assert pos.flags == ["short_quote"]


# --------------------------------------------------------------------------- #
# ReviewDB — Initialisierung & Validierung
# --------------------------------------------------------------------------- #


class TestReviewDBInit:
    def test_missing_database_url_raises(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        with pytest.raises(RuntimeError, match="DATABASE_URL"):
            ReviewDB()

    def test_uses_explicit_url(self):
        db = ReviewDB(database_url="postgresql://x:y@localhost/z")
        assert db.database_url == "postgresql://x:y@localhost/z"

    def test_uses_env_url(self, env_db):
        db = ReviewDB()
        assert "wahlkompass" in db.database_url


# --------------------------------------------------------------------------- #
# ReviewDB — Lesezugriffe (mit gemockter Connection)
# --------------------------------------------------------------------------- #


class TestReviewDBReads:
    def test_list_seasons_returns_dicts(self, env_db):
        db = ReviewDB()
        fake_cursor = mock.MagicMock()
        fake_cursor.fetchall.return_value = [
            {"id": "btw2025", "type": "bundestag", "date": "2025-02-23",
             "region": "Bund", "phase": "erfassung"},
        ]
        fake_conn = mock.MagicMock()
        fake_conn.cursor.return_value.__enter__.return_value = fake_cursor
        with mock.patch.object(db, "connect") as mock_ctx:
            mock_ctx.return_value.__enter__.return_value = fake_conn
            mock_ctx.return_value.__exit__.return_value = False
            seasons = db.list_seasons()
        assert len(seasons) == 1
        assert seasons[0]["id"] == "btw2025"

    def test_list_flagged_returns_flagged_positions(self, env_db):
        db = ReviewDB()
        fake_cursor = mock.MagicMock()
        fake_cursor.fetchall.return_value = [
            {
                "id": "pos-1", "party_name": "SPD",
                "thesis_statement": "These A", "position_type": "zustimmen",
                "review_status": "pending", "flags": ["missing_evidence"],
                "beleg_quote": None, "beleg_source": None,
                "beleg_page": None, "beleg_url": None,
            },
        ]
        fake_conn = mock.MagicMock()
        fake_conn.cursor.return_value.__enter__.return_value = fake_cursor
        with mock.patch.object(db, "connect") as mock_ctx:
            mock_ctx.return_value.__enter__.return_value = fake_conn
            mock_ctx.return_value.__exit__.return_value = False
            flagged = db.list_flagged("btw2025")
        assert len(flagged) == 1
        assert isinstance(flagged[0], FlaggedPosition)
        assert flagged[0].flags == ["missing_evidence"]

    def test_get_flagged_count(self, env_db):
        db = ReviewDB()
        fake_cursor = mock.MagicMock()
        fake_cursor.fetchone.return_value = (7,)
        fake_conn = mock.MagicMock()
        fake_conn.cursor.return_value.__enter__.return_value = fake_cursor
        with mock.patch.object(db, "connect") as mock_ctx:
            mock_ctx.return_value.__enter__.return_value = fake_conn
            mock_ctx.return_value.__exit__.return_value = False
            count = db.get_flagged_count("btw2025")
        assert count == 7


# --------------------------------------------------------------------------- #
# ReviewDB — Schreibzugriffe & Audit-Log
# --------------------------------------------------------------------------- #


class TestReviewDBWrites:
    def test_update_review_status_validates_status(self, env_db):
        db = ReviewDB()
        with pytest.raises(ValueError, match="Ungültiger review_status"):
            db.update_review_status("pos-1", "bogus", "reviewer")

    def test_update_review_status_writes_log(self, env_db):
        db = ReviewDB()
        before = {"id": "pos-1", "position_type": "zustimmen",
                  "review_status": "pending", "flags": []}
        after = {"id": "pos-1", "position_type": "zustimmen",
                 "review_status": "solo-geprueft", "flags": []}
        fake_cursor = mock.MagicMock()
        # _current_state: returns 'before' first, 'after' second
        fake_cursor.fetchone.side_effect = [before, after]
        fake_conn = mock.MagicMock()
        fake_conn.cursor.return_value.__enter__.return_value = fake_cursor
        with mock.patch.object(db, "connect") as mock_ctx:
            mock_ctx.return_value.__enter__.return_value = fake_conn
            mock_ctx.return_value.__exit__.return_value = False
            db.update_review_status("pos-1", "solo-geprueft", "alice")
        # Mindestens 2 execute-Aufrufe: UPDATE + INSERT log
        assert fake_cursor.execute.call_count >= 2
        # Letzter Aufruf sollte INSERT INTO review_log sein
        last_sql = fake_cursor.execute.call_args_list[-1].args[0]
        assert "INSERT INTO review_log" in last_sql

    def test_set_position_type_validates_type(self, env_db):
        db = ReviewDB()
        with pytest.raises(ValueError, match="Ungültiger position_type"):
            db.set_position_type("pos-1", "bogus", "reviewer")

    def test_set_position_type_sets_solo_geprueft(self, env_db):
        db = ReviewDB()
        before = {"id": "pos-1", "position_type": "zustimmen",
                  "review_status": "pending", "flags": ["missing_evidence"]}
        after = {"id": "pos-1", "position_type": "unklar",
                 "review_status": "solo-geprueft", "flags": ["missing_evidence"]}
        fake_cursor = mock.MagicMock()
        fake_cursor.fetchone.side_effect = [before, after]
        fake_conn = mock.MagicMock()
        fake_conn.cursor.return_value.__enter__.return_value = fake_cursor
        with mock.patch.object(db, "connect") as mock_ctx:
            mock_ctx.return_value.__enter__.return_value = fake_conn
            mock_ctx.return_value.__exit__.return_value = False
            db.set_position_type("pos-1", "unklar", "bob")
        # Aufruf-Reihenfolge: SELECT (before) → UPDATE → SELECT (after) → INSERT log
        executed_sqls = [
            call.args[0] for call in fake_cursor.execute.call_args_list
        ]
        update_calls = [
            call for call in fake_cursor.execute.call_args_list
            if "UPDATE position" in call.args[0]
        ]
        assert len(update_calls) == 1
        # position_type 'unklar' wird als Parameter übergeben
        params = update_calls[0].args[1]
        assert params[0] == "unklar"
        assert params[1] == "pos-1"
        assert "solo-geprueft" in update_calls[0].args[0]

    def test_update_beleg_rejects_short_quote(self, env_db):
        db = ReviewDB()
        with pytest.raises(ValueError, match="zu kurz"):
            db.update_beleg("pos-1", "kurz", "src", None, None, "rev")

    def test_update_beleg_rejects_long_quote(self, env_db):
        db = ReviewDB()
        long_quote = "x" * 301
        with pytest.raises(ValueError, match="zu lang"):
            db.update_beleg("pos-1", long_quote, "src", None, None, "rev")

    def test_update_beleg_rejects_empty_source(self, env_db):
        db = ReviewDB()
        quote = "x" * 25
        with pytest.raises(ValueError, match="Quelle"):
            db.update_beleg("pos-1", quote, "   ", None, None, "rev")

    def test_mark_for_reextraction_adds_flag(self, env_db):
        db = ReviewDB()
        before = {"id": "pos-1", "position_type": "zustimmen",
                  "review_status": "pending", "flags": []}
        after = {"id": "pos-1", "position_type": "zustimmen",
                 "review_status": "re-extraction",
                 "flags": ["re-extraction-requested"]}
        fake_cursor = mock.MagicMock()
        fake_cursor.fetchone.side_effect = [before, after]
        fake_conn = mock.MagicMock()
        fake_conn.cursor.return_value.__enter__.return_value = fake_cursor
        with mock.patch.object(db, "connect") as mock_ctx:
            mock_ctx.return_value.__enter__.return_value = fake_conn
            mock_ctx.return_value.__exit__.return_value = False
            db.mark_for_reextraction("pos-1", "carol")
        # Aufruf-Reihenfolge: SELECT (before) → UPDATE → SELECT (after) → INSERT log
        executed_sqls = [
            call.args[0] for call in fake_cursor.execute.call_args_list
        ]
        update_sqls = [s for s in executed_sqls if "UPDATE position" in s]
        assert len(update_sqls) == 1
        assert "re-extraction" in update_sqls[0]
        assert "re-extraction-requested" in update_sqls[0]

    def test_update_review_status_unknown_position(self, env_db):
        db = ReviewDB()
        fake_cursor = mock.MagicMock()
        fake_cursor.fetchone.return_value = None  # _current_state: nichts
        fake_conn = mock.MagicMock()
        fake_conn.cursor.return_value.__enter__.return_value = fake_cursor
        with mock.patch.object(db, "connect") as mock_ctx:
            mock_ctx.return_value.__enter__.return_value = fake_conn
            mock_ctx.return_value.__exit__.return_value = False
            with pytest.raises(ValueError, match="nicht gefunden"):
                db.update_review_status("nope", "solo-geprueft", "rev")


# --------------------------------------------------------------------------- #
# ReviewDB — Batch
# --------------------------------------------------------------------------- #


class TestReviewDBBatch:
    def test_batch_returns_zero_when_no_matches(self, env_db):
        db = ReviewDB()
        fake_cursor = mock.MagicMock()
        fake_cursor.fetchall.return_value = []
        fake_conn = mock.MagicMock()
        fake_conn.cursor.return_value.__enter__.return_value = fake_cursor
        with mock.patch.object(db, "connect") as mock_ctx:
            mock_ctx.return_value.__enter__.return_value = fake_conn
            mock_ctx.return_value.__exit__.return_value = False
            count = db.batch_set_unklar_for_party(
                "btw2025", "spd", "missing_evidence", "reviewer"
            )
        assert count == 0

    def test_batch_updates_all_matching(self, env_db):
        db = ReviewDB()
        rows = [
            {"id": "pos-1", "position_type": "zustimmen",
             "review_status": "pending", "flags": ["missing_evidence"]},
            {"id": "pos-2", "position_type": "ablehnen",
             "review_status": "pending", "flags": ["missing_evidence"]},
        ]
        fake_cursor = mock.MagicMock()
        fake_cursor.fetchall.return_value = rows
        # _current_state-Aufrufe pro Position
        fake_cursor.fetchone.return_value = rows[0]
        fake_conn = mock.MagicMock()
        fake_conn.cursor.return_value.__enter__.return_value = fake_cursor
        with mock.patch.object(db, "connect") as mock_ctx:
            mock_ctx.return_value.__enter__.return_value = fake_conn
            mock_ctx.return_value.__exit__.return_value = False
            count = db.batch_set_unklar_for_party(
                "btw2025", "spd", "missing_evidence", "reviewer"
            )
        assert count == 2


# --------------------------------------------------------------------------- #
# CLI-Befehle (über CliRunner)
# --------------------------------------------------------------------------- #


class TestCLICommands:
    def test_review_no_flagged(self, env_db, runner):
        with mock.patch("review.cli.ReviewDB") as MockDB:
            MockDB.return_value.list_seasons.return_value = [
                {"id": "btw2025", "type": "bundestag", "date": "2025-02-23",
                 "region": "Bund", "phase": "erfassung"},
            ]
            MockDB.return_value.list_flagged.return_value = []
            result = runner.invoke(cli, ["review", "-s", "btw2025", "-r", "alice"])
        assert result.exit_code == 0
        assert "Keine markierten Positionen" in result.output

    def test_review_with_flagged_freigeben(self, env_db, runner):
        pos = _make_position()
        with mock.patch("review.cli.ReviewDB") as MockDB:
            MockDB.return_value.list_flagged.return_value = [pos]
            result = runner.invoke(
                cli, ["review", "-s", "btw2025", "-r", "alice"],
                input="1\n",  # Aktion: freigeben
            )
        assert result.exit_code == 0, result.output
        MockDB.return_value.update_review_status.assert_called_once_with(
            "pos-1", "solo-geprueft", "alice",
            note="Solo-Review: freigegeben",
        )
        assert "freigegeben" in result.output

    def test_review_with_flagged_unklar(self, env_db, runner):
        pos = _make_position()
        with mock.patch("review.cli.ReviewDB") as MockDB:
            MockDB.return_value.list_flagged.return_value = [pos]
            result = runner.invoke(
                cli, ["review", "-s", "btw2025", "-r", "bob"],
                input="3\n",  # Aktion: unklar
            )
        assert result.exit_code == 0, result.output
        MockDB.return_value.set_position_type.assert_called_once_with(
            "pos-1", "unklar", "bob",
            note="Solo-Review: auf unklar gesetzt",
        )

    def test_review_with_flagged_reextraction(self, env_db, runner):
        pos = _make_position()
        with mock.patch("review.cli.ReviewDB") as MockDB:
            MockDB.return_value.list_flagged.return_value = [pos]
            result = runner.invoke(
                cli, ["review", "-s", "btw2025", "-r", "carol"],
                input="4\n",  # Aktion: reextraction
            )
        assert result.exit_code == 0, result.output
        MockDB.return_value.mark_for_reextraction.assert_called_once_with(
            "pos-1", "carol", note="Solo-Review: zurück an KI-Extraktion",
        )

    def test_review_skip(self, env_db, runner):
        pos = _make_position()
        with mock.patch("review.cli.ReviewDB") as MockDB:
            MockDB.return_value.list_flagged.return_value = [pos]
            result = runner.invoke(
                cli, ["review", "-s", "btw2025", "-r", "dan"],
                input="s\n",  # skip
            )
        assert result.exit_code == 0, result.output
        assert "übersprungen" in result.output
        MockDB.return_value.update_review_status.assert_not_called()

    def test_review_quit(self, env_db, runner):
        pos1 = _make_position(id="pos-1")
        pos2 = _make_position(id="pos-2", party_name="CDU")
        with mock.patch("review.cli.ReviewDB") as MockDB:
            MockDB.return_value.list_flagged.return_value = [pos1, pos2]
            result = runner.invoke(
                cli, ["review", "-s", "btw2025", "-r", "eve"],
                input="q\n",
            )
        assert result.exit_code == 0, result.output
        assert "abgebrochen" in result.output

    def test_review_missing_database_url(self, monkeypatch, runner):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        result = runner.invoke(cli, ["review", "-s", "btw2025"])
        assert result.exit_code == 2
        assert "DATABASE_URL" in result.output

    def test_list_seasons(self, env_db, runner):
        with mock.patch("review.cli.ReviewDB") as MockDB:
            MockDB.return_value.list_seasons.return_value = [
                {"id": "btw2025", "type": "bundestag", "date": "2025-02-23",
                 "region": "Bund", "phase": "erfassung"},
            ]
            result = runner.invoke(cli, ["list-seasons"])
        assert result.exit_code == 0
        assert "btw2025" in result.output

    def test_list_flagged(self, env_db, runner):
        pos = _make_position()
        with mock.patch("review.cli.ReviewDB") as MockDB:
            MockDB.return_value.list_flagged.return_value = [pos]
            result = runner.invoke(cli, ["list-flagged", "-s", "btw2025"])
        assert result.exit_code == 0
        assert "SPD" in result.output
        assert "missing_evidence" in result.output

    def test_batch_unklar(self, env_db, runner):
        with mock.patch("review.cli.ReviewDB") as MockDB:
            MockDB.return_value.batch_set_unklar_for_party.return_value = 3
            result = runner.invoke(
                cli, [
                    "batch-unklar", "-s", "btw2025", "-p", "spd",
                    "-f", "missing_evidence", "-r", "alice",
                ],
            )
        assert result.exit_code == 0, result.output
        assert "3 Position" in result.output
        MockDB.return_value.batch_set_unklar_for_party.assert_called_once()

    def test_batch_unklar_unknown_flag_aborts(self, env_db, runner):
        with mock.patch("review.cli.ReviewDB") as MockDB:
            MockDB.return_value.batch_set_unklar_for_party.return_value = 0
            result = runner.invoke(
                cli, [
                    "batch-unklar", "-s", "btw2025", "-p", "spd",
                    "-f", "unknown_flag", "-r", "alice",
                ],
                input="n\n",  # nicht fortfahren
            )
        assert result.exit_code == 0
        MockDB.return_value.batch_set_unklar_for_party.assert_not_called()

    def test_log_command(self, env_db, runner):
        with mock.patch("review.cli.ReviewDB") as MockDB:
            MockDB.return_value.list_log.return_value = [
                {
                    "id": "log-1", "action": "freigeben", "reviewer": "alice",
                    "note": "Solo-Review: freigegeben",
                    "before_state": '{"review_status": "pending"}',
                    "after_state": '{"review_status": "solo-geprueft"}',
                    "created_at": "2026-06-27T10:00:00+00:00",
                },
            ]
            result = runner.invoke(cli, ["log", "pos-1"])
        assert result.exit_code == 0
        assert "alice" in result.output
        assert "freigeben" in result.output

    def test_log_empty(self, env_db, runner):
        with mock.patch("review.cli.ReviewDB") as MockDB:
            MockDB.return_value.list_log.return_value = []
            result = runner.invoke(cli, ["log", "pos-1"])
        assert result.exit_code == 0
        assert "Keine Log-Einträge" in result.output

    def test_freigeben_command(self, env_db, runner):
        with mock.patch("review.cli.ReviewDB") as MockDB:
            result = runner.invoke(
                cli, ["freigeben", "pos-1", "-r", "alice"],
            )
        assert result.exit_code == 0, result.output
        MockDB.return_value.update_review_status.assert_called_once_with(
            "pos-1", "solo-geprueft", "alice",
            note="CLI: direkt freigegeben",
        )


# --------------------------------------------------------------------------- #
# Konstanten-Integrität
# --------------------------------------------------------------------------- #


class TestConstants:
    def test_position_types_complete(self):
        assert VALID_POSITION_TYPES == {
            "zustimmen", "ablehnen", "neutral", "unklar"
        }

    def test_review_statuses_complete(self):
        assert VALID_REVIEW_STATUSES == {
            "pending", "solo-geprueft", "re-extraction", "community-geprueft",
        }

    def test_known_flags_contains_missing_evidence(self):
        assert "missing_evidence" in KNOWN_FLAGS
