"""
Tests für die Auto-Validierung (AP4).
Testet alle 6 Prüfkriterien aus §B.1.1.
"""
import json
from datetime import datetime, timezone
from packages.extraction.src.auto_validate import (
    validate_position,
    validate_all_positions,
    generate_validation_report,
    VALID_POSITION_TYPES,
    SENSITIVE_CATEGORIES,
)


def make_position(position_type="zustimmen", position_id="pos-1"):
    return {
        "id": position_id,
        "party_id": "party-spd",
        "thesis_id": "the-btw2025-wirt-1",
        "program_id": "prog-1",
        "position_type": position_type,
    }


_SENTINEL = object()

def make_evidence(quote="Dies ist ein Testzitat mit genügend Länge.", quote_location=_SENTINEL):
    if quote_location is _SENTINEL:
        quote_location = {"page": 5, "char_offset": 100}
    return {
        "position_id": "pos-1",
        "quote": quote,
        "quote_location": quote_location,
    }


class TestCheck1MissingEvidence:
    """Check 1: Beleg vorhanden (missing_evidence)"""

    def test_valid_position_with_evidence_passes(self):
        pos = make_position("zustimmen")
        ev = make_evidence()
        report = validate_position(pos, ev, "Dies ist ein Testzitat mit genügend Länge.")
        assert "missing_evidence" not in report["flag_reasons"]

    def test_valid_position_without_evidence_fails(self):
        pos = make_position("zustimmen")
        report = validate_position(pos, None, "")
        assert "missing_evidence" in report["flag_reasons"]

    def test_unklar_without_evidence_passes(self):
        pos = make_position("unklar")
        report = validate_position(pos, None, "")
        assert "missing_evidence" not in report["flag_reasons"]
        assert report["status"] == "auto-validiert"


class TestCheck2QuoteMismatch:
    """Check 2: Zitat matcht Quelle (quote_mismatch)"""

    def test_matching_quote_passes(self):
        program_text = "Wir unterstützen die Schuldenbremse ausdrücklich."
        pos = make_position("zustimmen")
        ev = make_evidence(quote="Wir unterstützen die Schuldenbremse ausdrücklich.")
        report = validate_position(pos, ev, program_text)
        assert "quote_mismatch" not in report["flag_reasons"]

    def test_non_matching_quote_fails(self):
        program_text = "Das ist der eigentliche Programmtext."
        pos = make_position("zustimmen")
        ev = make_evidence(quote="Diesen Text gibt es nicht im Programm.")
        report = validate_position(pos, ev, program_text)
        assert "quote_mismatch" in report["flag_reasons"]


class TestCheck3FormatError:
    """Check 3: Format korrekt (format_error)"""

    def test_valid_pdf_location_passes(self):
        pos = make_position("zustimmen")
        ev = make_evidence(quote_location={"page": 3, "char_offset": 42})
        report = validate_position(pos, ev, "x" * 50)
        assert "format_error" not in report["flag_reasons"]

    def test_valid_html_location_passes(self):
        pos = make_position("zustimmen")
        ev = make_evidence(quote_location={"url": "https://example.com/programm", "css_selector": "#klima > p"})
        report = validate_position(pos, ev, "x" * 50)
        assert "format_error" not in report["flag_reasons"]

    def test_empty_location_fails(self):
        pos = make_position("zustimmen")
        matching_quote = "Dies ist ein Testzitat mit genügend Länge."
        ev = make_evidence(quote=matching_quote, quote_location=None)
        report = validate_position(pos, ev, matching_quote)
        assert "format_error" in report["flag_reasons"]

    def test_wrong_format_location_fails(self):
        pos = make_position("zustimmen")
        ev = make_evidence(quote_location={"wrong_key": "value"})
        report = validate_position(pos, ev, "x" * 50)
        assert "format_error" in report["flag_reasons"]


class TestCheck4QuoteLength:
    """Check 4: Zitatlänge 20-300 (quote_length_violation)"""

    def test_valid_length_passes(self):
        pos = make_position("zustimmen")
        ev = make_evidence(quote="Dies ist ein Zitat mit genau der richtigen Länge für den Test.")
        report = validate_position(pos, ev, "Dies ist ein Zitat mit genau der richtigen Länge für den Test.")
        assert "quote_length_violation" not in report["flag_reasons"]

    def test_too_short_fails(self):
        pos = make_position("zustimmen")
        ev = make_evidence(quote="Zu kurz.")
        report = validate_position(pos, ev, "Zu kurz.")
        assert "quote_length_violation" in report["flag_reasons"]

    def test_too_long_fails(self):
        pos = make_position("zustimmen")
        long_quote = "A" * 301
        ev = make_evidence(quote=long_quote)
        report = validate_position(pos, ev, long_quote)
        assert "quote_length_violation" in report["flag_reasons"]

    def test_min_boundary_passes(self):
        pos = make_position("zustimmen")
        quote = "A" * 20
        ev = make_evidence(quote=quote)
        report = validate_position(pos, ev, quote)
        assert "quote_length_violation" not in report["flag_reasons"]

    def test_max_boundary_passes(self):
        pos = make_position("zustimmen")
        quote = "A" * 300
        ev = make_evidence(quote=quote)
        report = validate_position(pos, ev, quote)
        assert "quote_length_violation" not in report["flag_reasons"]


class TestCheck6InvalidPositionType:
    """Check 6: Positions-Typ gültig (invalid_position_type)"""

    def test_valid_types_pass(self):
        for ptype in VALID_POSITION_TYPES:
            pos = make_position(ptype)
            ev = make_evidence() if ptype != "unklar" else None
            report = validate_position(pos, ev, "x" * 50)
            assert "invalid_position_type" not in report["flag_reasons"], f"Failed for {ptype}"

    def test_invalid_type_fails(self):
        pos = make_position("vielleicht")
        report = validate_position(pos, None, "")
        assert "invalid_position_type" in report["flag_reasons"]


class TestSensitiveCategories:
    """§B.1.3: Sensible Rubriken immer geflaggt"""

    def test_sensitive_category_always_flagged(self):
        pos = make_position("zustimmen")
        ev = make_evidence()
        report = validate_position(
            pos, ev, "x" * 50,
            category_name="Migration und Integration",
            is_sensitive=True,
        )
        assert "sensitive_category" in report["flag_reasons"]
        assert report["status"] == "geflaggt"

    def test_non_sensitive_category_not_flagged_for_sensitive_reason(self):
        pos = make_position("zustimmen")
        ev = make_evidence()
        report = validate_position(
            pos, ev, "x" * 50,
            category_name="Wirtschaft und Finanzen",
            is_sensitive=False,
        )
        assert "sensitive_category" not in report["flag_reasons"]

    def test_all_sensitive_categories(self):
        for cat in SENSITIVE_CATEGORIES:
            pos = make_position("zustimmen")
            ev = make_evidence()
            report = validate_position(pos, ev, "x" * 50, category_name=cat)
            assert "sensitive_category" in report["flag_reasons"], f"Failed for {cat}"


class TestValidateAllPositions:
    """Test batch validation incl. contradiction check (Check 5)"""

    def test_contradiction_detected(self):
        positions = [
            {"id": "pos-1", "party_id": "party-spd", "thesis_id": "the-1",
             "program_id": "prog-1", "position_type": "zustimmen"},
            {"id": "pos-2", "party_id": "party-spd", "thesis_id": "the-1",
             "program_id": "prog-1", "position_type": "ablehnen"},
        ]
        evidences = {
            "pos-1": make_evidence(),
            "pos-2": make_evidence(),
        }
        reports = validate_all_positions(positions, evidences, {"prog-1": "x" * 50}, {})
        for r in reports:
            assert "internal_contradiction" in r["flag_reasons"]

    def test_no_contradiction_when_consistent(self):
        positions = [
            {"id": "pos-1", "party_id": "party-spd", "thesis_id": "the-1",
             "program_id": "prog-1", "position_type": "zustimmen"},
            {"id": "pos-2", "party_id": "party-cdu", "thesis_id": "the-1",
             "program_id": "prog-2", "position_type": "ablehnen"},
        ]
        evidences = {
            "pos-1": make_evidence(),
            "pos-2": make_evidence(),
        }
        reports = validate_all_positions(positions, evidences,
                                          {"prog-1": "x" * 50, "prog-2": "x" * 50}, {})
        for r in reports:
            assert "internal_contradiction" not in r["flag_reasons"]


class TestGenerateReport:
    """Test report generation"""

    def test_empty_report(self):
        report = generate_validation_report([])
        assert report["total"] == 0

    def test_report_with_mixed_status(self):
        reports = [
            {"status": "auto-validiert", "flag_reasons": []},
            {"status": "geflaggt", "flag_reasons": ["missing_evidence"]},
            {"status": "geflaggt", "flag_reasons": ["missing_evidence", "quote_mismatch"]},
        ]
        summary = generate_validation_report(reports)
        assert summary["total"] == 3
        assert summary["auto_validiert"] == 1
        assert summary["geflaggt"] == 2
        assert summary["flag_rate"] == 66.7
        assert summary["flag_reasons_breakdown"]["missing_evidence"] == 2
        assert summary["flag_reasons_breakdown"]["quote_mismatch"] == 1
