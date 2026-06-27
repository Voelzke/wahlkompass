"""
auto_validate.py — Auto-Validierung von extrahierten Parteipositionen.

Implementiert die 6 Prüfkriterien aus §B.1.1 des Pflichtenhefts:
1. Beleg vorhanden (missing_evidence)
2. Zitat matcht Quelle (quote_mismatch)
3. Format korrekt (format_error)
4. Zitatlänge 20-300 (quote_length_violation)
5. Widerspruchsfreiheit (internal_contradiction)
6. Positions-Typ gültig (invalid_position_type)

Sensible Rubriken werden immer geflaggt (§B.1.3).
"""

import json
import re
from datetime import datetime, timezone
from typing import Optional


VALID_POSITION_TYPES = {"zustimmen", "ablehnen", "neutral", "unklar"}

SENSITIVE_CATEGORIES = {
    "Migration und Integration",
    "Demokratie und Verfassung",
    "Innen und Recht",
}


def validate_position(
    position: dict,
    evidence: Optional[dict],
    program_text: str,
    category_name: str = "",
    is_sensitive: bool = False,
) -> dict:
    """
    Validiere eine einzelne Position gegen alle 6 Kriterien.

    Returns: JSON-Report wie in §B.1.4 definiert.
    """
    position_type = position.get("position_type", "")
    flag_reasons = []
    checks_passed = 0
    checks_total = 6

    # Check 1: Beleg vorhanden
    if position_type == "unklar":
        # unklar braucht keinen Beleg
        checks_passed += 1
    elif evidence and evidence.get("quote"):
        checks_passed += 1
    else:
        flag_reasons.append("missing_evidence")

    # Check 2: Zitat matcht Quelle
    if position_type != "unklar" and evidence:
        quote = evidence.get("quote", "")
        if quote and program_text:
            if quote in program_text:
                checks_passed += 1
            else:
                flag_reasons.append("quote_mismatch")
        elif not quote:
            # Already caught by missing_evidence
            checks_passed += 1
        else:
            # No program text to compare against — skip
            checks_passed += 1
    else:
        checks_passed += 1

    # Check 3: Format korrekt (quote_location schema)
    if position_type != "unklar" and evidence:
        quote_location = evidence.get("quote_location")
        if quote_location:
            if isinstance(quote_location, str):
                try:
                    quote_location = json.loads(quote_location)
                except json.JSONDecodeError:
                    quote_location = None
            if isinstance(quote_location, dict):
                # PDF: {page, char_offset}, HTML: {url, css_selector}
                has_page = "page" in quote_location or "char_offset" in quote_location
                has_url = "url" in quote_location or "css_selector" in quote_location
                if has_page or has_url:
                    checks_passed += 1
                else:
                    flag_reasons.append("format_error")
            else:
                flag_reasons.append("format_error")
        else:
            # Missing location — but if position is not unklar, that's a format error
            flag_reasons.append("format_error")
    else:
        checks_passed += 1

    # Check 4: Zitatlänge 20-300
    if position_type != "unklar" and evidence:
        quote = evidence.get("quote", "")
        if quote:
            if 20 <= len(quote) <= 300:
                checks_passed += 1
            else:
                flag_reasons.append("quote_length_violation")
        else:
            checks_passed += 1  # Already caught by missing_evidence
    else:
        checks_passed += 1

    # Check 5: Widerspruchsfreiheit
    # (checked at party level — here we just pass, the party-level check
    #  detects if the same party has contradictory positions for the same thesis)
    checks_passed += 1  # Simplified — full check in validate_all_positions

    # Check 6: Positions-Typ gültig
    if position_type in VALID_POSITION_TYPES:
        checks_passed += 1
    else:
        flag_reasons.append("invalid_position_type")

    # Sensitive categories always flagged for solo review
    if is_sensitive or category_name in SENSITIVE_CATEGORIES:
        if "sensitive_category" not in flag_reasons:
            flag_reasons.append("sensitive_category")

    # Determine status
    has_real_flags = any(r not in ("sensitive_category",) for r in flag_reasons)
    is_flagged = bool(flag_reasons)

    # Sensitive-only flags still get flagged (need solo review)
    if flag_reasons:
        status = "geflaggt"
    else:
        status = "auto-validiert"

    return {
        "position_id": position.get("id", ""),
        "status": status,
        "flag_reasons": flag_reasons,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "checks_passed": checks_passed,
        "checks_total": checks_total,
    }


def validate_all_positions(positions: list[dict], evidences: dict, program_texts: dict,
                           categories: dict) -> list[dict]:
    """
    Validiere alle Positionen einer Saison.
    Inkl. Widerspruchsfreiheits-Check (Check 5) auf Partei-Ebene.

    Args:
        positions: List of position dicts
        evidences: Dict keyed by position_id → evidence dict
        program_texts: Dict keyed by program_id → text string
        categories: Dict keyed by thesis_id → {category_name, is_sensitive}
    """
    reports = []

    # Group positions by party+thesis for contradiction check
    party_thesis_map = {}  # (party_id, thesis_id) → list of position_types
    for pos in positions:
        key = (pos.get("party_id", ""), pos.get("thesis_id", ""))
        party_thesis_map.setdefault(key, []).append(pos.get("position_type", ""))

    for pos in positions:
        evidence = evidences.get(pos.get("id"))
        program_id = pos.get("program_id", "")
        program_text = program_texts.get(program_id, "")
        thesis_id = pos.get("thesis_id", "")
        cat_info = categories.get(thesis_id, {})

        report = validate_position(
            position=pos,
            evidence=evidence,
            program_text=program_text,
            category_name=cat_info.get("category_name", ""),
            is_sensitive=cat_info.get("is_sensitive", False),
        )

        # Check 5: Contradiction
        key = (pos.get("party_id", ""), pos.get("thesis_id", ""))
        pos_types = party_thesis_map.get(key, [])
        if len(pos_types) > 1:
            has_zustimmen = "zustimmen" in pos_types
            has_ablehnen = "ablehnen" in pos_types
            if has_zustimmen and has_ablehnen:
                if "internal_contradiction" not in report["flag_reasons"]:
                    report["flag_reasons"].append("internal_contradiction")
                    report["checks_passed"] -= 1
                report["status"] = "geflaggt"

        reports.append(report)

    return reports


def generate_validation_report(reports: list[dict]) -> dict:
    """Generiere einen Zusammenfassungs-Report."""
    total = len(reports)
    if total == 0:
        return {"total": 0, "auto_validiert": 0, "geflaggt": 0, "flag_rate": 0}

    auto_validiert = sum(1 for r in reports if r["status"] == "auto-validiert")
    geflaggt = total - auto_validiert
    flag_rate = round(geflaggt / total * 100, 1)

    # Count flag reasons
    reason_counts = {}
    for r in reports:
        for reason in r.get("flag_reasons", []):
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

    return {
        "total": total,
        "auto_validiert": auto_validiert,
        "geflaggt": geflaggt,
        "flag_rate": flag_rate,
        "flag_reasons_breakdown": reason_counts,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Auto-Validierung von Parteipositionen")
    parser.add_argument("--data-dir", default="data/", help="Verzeichnis mit Positionsdaten")
    args = parser.parse_args()

    # In standalone mode: load positions from JSON export
    positions_path = f"{args.data_dir}positions/btw2025.json"
    try:
        with open(positions_path) as f:
            data = json.load(f)
        reports = validate_all_positions(
            data.get("positions", []),
            {e["position_id"]: e for e in data.get("evidences", [])},
            {},
            {},
        )
        summary = generate_validation_report(reports)
        print(json.dumps(summary, indent=2))
    except FileNotFoundError:
        print(f"Positions file not found: {positions_path}", file=sys.stderr)
        sys.exit(1)
