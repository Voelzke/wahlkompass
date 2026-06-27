"""Review-CLI für die Solo-Prüfung markierter Parteipositionen (AP5).

Interaktives Kommandozeilen-Tool für den Review-Prozess. Es listet alle
markierten Positionen einer Saison auf und bietet pro Position die Aktionen:

* **freigeben** — ``review_status`` auf 'solo-geprueft' setzen
* **korrigieren** — Beleg (Zitat + Quelle) editieren, dann 'solo-geprueft'
* **auf unklar setzen** — ``position_type`` auf 'unklar' setzen
* **zurueck an KI-Extraktion** — für erneute Extraktion markieren

Zusätzlich: Batch-Aktion, um alle ``missing_evidence``-Flags einer Partei
auf 'unklar' zu setzen.

Jede Entscheidung wird in die ``review_log``-Tabelle geschrieben (Audit-Trail).

Verwendung
----------

.. code-block:: bash

    # Datenbank-URL setzen
    export DATABASE_URL="postgresql://wahlkompass:***@localhost:5432/wahlkompass"

    # Saison wählen und Review starten
    python -m review.cli review

    # Direkt für eine bestimmte Saison
    python -m review.cli review --season btw2025

    # Batch: alle missing_evidence-Flags einer Partei auf unklar
    python -m review.cli batch-unklar --season btw2025 \\
        --party spd --flag missing_evidence

    # Audit-Trail für eine Position
    python -m review.cli log <position-id>

Framework: Click. Verbindung via ``DATABASE_URL`` (PostgreSQL).
"""

from __future__ import annotations

import os
import sys
from typing import Optional

import click

from review.db import (
    KNOWN_FLAGS,
    VALID_POSITION_TYPES,
    ReviewDB,
)


# --------------------------------------------------------------------------- #
# Hilfsfunktionen
# --------------------------------------------------------------------------- #

#: Nummerierung der Einzelaktionen im Review-Loop.
ACTIONS = {
    "1": "freigeben",
    "2": "korrigieren",
    "3": "unklar",
    "4": "reextraction",
    "s": "skip",
    "q": "quit",
}

ACTION_LABELS = {
    "1": "[1] Freigeben (solo-geprueft)",
    "2": "[2] Korrigieren (Beleg/Position editieren)",
    "3": "[3] Auf unklar setzen",
    "4": "[4] Zurueck an KI-Extraktion",
    "s": "[s] Überspringen",
    "q": "[q] Review beenden",
}


def _get_db() -> ReviewDB:
    """Erzeugt eine ReviewDB-Instanz oder bricht mit klarer Meldung ab."""
    try:
        return ReviewDB()
    except RuntimeError as exc:
        click.echo(f"FEHLER: {exc}", err=True)
        sys.exit(2)


def _print_position(pos, index: Optional[int] = None,
                    total: Optional[int] = None) -> None:
    """Gibt eine Position formatiert auf der Konsole aus."""
    prefix = ""
    if index is not None and total is not None:
        prefix = f"\n{'='*70}\nPosition {index}/{total}\n"
    else:
        prefix = f"\n{'='*70}"
    click.echo(prefix)
    click.echo(f"  Partei:       {pos.party_name}")
    click.echo(f"  These:        {pos.thesis_statement}")
    click.echo(f"  Position:     {pos.position_type}")
    click.echo(f"  Review-Status:{pos.review_status}")
    flags_str = ", ".join(pos.flags) if pos.flags else "(keine)"
    click.echo(f"  Flags:        {flags_str}")
    click.echo(f"  Beleg-Zitat:  {pos.beleg_quote or '(kein Beleg)'}")
    source_parts = []
    if pos.beleg_source:
        source_parts.append(pos.beleg_source)
    if pos.beleg_page:
        source_parts.append(f"S. {pos.beleg_page}")
    if pos.beleg_url:
        source_parts.append(pos.beleg_url)
    source_str = " | ".join(source_parts) if source_parts else "(keine Quelle)"
    click.echo(f"  Beleg-Quelle: {source_str}")
    click.echo(f"  Position-ID:  {pos.id}")


def _prompt_reviewer(default: str = "solo-reviewer") -> str:
    """Fragt den Reviewer-Namen ab (für den Audit-Trail)."""
    reviewer = os.environ.get("REVIEWER")
    if reviewer:
        return reviewer
    return click.prompt("Reviewer-Name", default=default, show_default=True)


def _prompt_action(pos) -> str:
    """Fragt die Aktion für eine Position ab."""
    click.echo("")
    for label in ACTION_LABELS.values():
        click.echo(f"  {label}")
    while True:
        choice = click.prompt(
            "Aktion", default="1", show_default=False
        ).strip().lower()
        if choice in ACTIONS:
            return ACTIONS[choice]
        click.echo(
            f"  Ungültige Eingabe '{choice}'. Bitte 1/2/3/4/s/q wählen.",
            err=True,
        )


def _prompt_new_beleg(pos) -> tuple[str, str, Optional[str], Optional[str]]:
    """Fragt die neuen Beleg-Daten für die Korrektur ab."""
    click.echo("\n  -- Korrektur des Belegs --")
    quote = click.prompt(
        "  Beleg-Zitat (min 20, max 300 Zeichen)",
        default=pos.beleg_quote or "",
    )
    if len(quote) < 20 or len(quote) > 300:
        click.echo(
            f"  Hinweis: Zitat hat {len(quote)} Zeichen "
            f"(erlaubt: 20–300).",
            err=True,
        )
    source = click.prompt(
        "  Beleg-Quelle (z.B. Wahlprogramm, Datei)",
        default=pos.beleg_source or "",
    )
    page = click.prompt(
        "  Seite (oder leer)", default=pos.beleg_page or "", show_default=False
    )
    url = click.prompt(
        "  URL (oder leer)", default=pos.beleg_url or "", show_default=False
    )
    return quote, source, page or None, url or None


def _prompt_position_type(default: str = "unklar") -> str:
    """Fragt einen neuen position_type ab."""
    click.echo(f"  Erlaubt: {sorted(VALID_POSITION_TYPES)}")
    while True:
        val = click.prompt(
            "  Neuer position_type", default=default, show_default=True
        ).strip().lower()
        if val in VALID_POSITION_TYPES:
            return val
        click.echo(f"  Ungültig: '{val}'. Erlaubt: {sorted(VALID_POSITION_TYPES)}",
                   err=True)


# --------------------------------------------------------------------------- #
# Click-Befehle
# --------------------------------------------------------------------------- #


@click.group()
def cli() -> None:
    """Review-CLI für die Solo-Prüfung markierter Parteipositionen."""


@cli.command()
@click.option(
    "--season", "-s",
    help="Saison-ID (z.B. btw2025). Ohne Angabe wird interaktiv gewählt.",
)
@click.option(
    "--reviewer", "-r",
    help="Reviewer-Name (alternativ Umgebungsvariable REVIEWER).",
)
def review(season: Optional[str], reviewer: Optional[str]) -> None:
    """Startet den interaktiven Review für eine Saison."""
    db = _get_db()
    reviewer = reviewer or _prompt_reviewer()

    # Saison wählen
    if not season:
        seasons = db.list_seasons()
        if not seasons:
            click.echo("Keine Saisons in der Datenbank gefunden.", err=True)
            sys.exit(1)
        click.echo("\nVerfügbare Saisons:")
        for i, s in enumerate(seasons, 1):
            click.echo(
                f"  [{i}] {s['id']}  ({s['type']} {s['date']}, {s['region']})"
            )
        idx = click.prompt(
            "Saison wählen", type=int, default=1, show_default=True
        )
        if idx < 1 or idx > len(seasons):
            click.echo("Ungültige Auswahl.", err=True)
            sys.exit(1)
        season = seasons[idx - 1]["id"]

    # Markierte Positionen laden
    flagged = db.list_flagged(season)
    if not flagged:
        click.echo(f"\nKeine markierten Positionen für Saison '{season}'. ✅")
        return

    total = len(flagged)
    click.echo(
        f"\n{total} markierte Position(en) für Saison '{season}'. "
        f"Reviewer: {reviewer}\n"
    )

    skipped: list[str] = []
    reviewed_count = 0
    for i, pos in enumerate(flagged, 1):
        _print_position(pos, i, total)
        action = _prompt_action(pos)

        if action == "quit":
            click.echo("\nReview abgebrochen durch Benutzer.")
            break
        if action == "skip":
            skipped.append(pos.id)
            click.echo("  → übersprungen.")
            continue

        try:
            if action == "freigeben":
                db.update_review_status(
                    pos.id, "solo-geprueft", reviewer,
                    note="Solo-Review: freigegeben",
                )
                click.echo("  → freigegeben (solo-geprueft).")
            elif action == "korrigieren":
                quote, source, page, url = _prompt_new_beleg(pos)
                new_pt = click.confirm(
                    "  position_type auch ändern?", default=False
                )
                if new_pt:
                    pos_type = _prompt_position_type(
                        default=pos.position_type
                    )
                else:
                    pos_type = None
                db.update_beleg(
                    pos.id, quote, source, page, url, reviewer,
                    note="Solo-Review: Beleg korrigiert",
                )
                if pos_type:
                    db.set_position_type(
                        pos.id, pos_type, reviewer,
                        note="Solo-Review: position_type korrigiert",
                    )
                click.echo("  → korrigiert und auf solo-geprueft gesetzt.")
            elif action == "unklar":
                db.set_position_type(
                    pos.id, "unklar", reviewer,
                    note="Solo-Review: auf unklar gesetzt",
                )
                click.echo("  → position_type=unklar, solo-geprueft.")
            elif action == "reextraction":
                db.mark_for_reextraction(
                    pos.id, reviewer,
                    note="Solo-Review: zurück an KI-Extraktion",
                )
                click.echo("  → zur erneuten KI-Extraktion markiert.")
        except ValueError as exc:
            click.echo(f"  FEHLER: {exc}", err=True)
            skipped.append(pos.id)
            continue
        except Exception as exc:  # noqa: BLE001
            click.echo(f"  Datenbankfehler: {exc}", err=True)
            skipped.append(pos.id)
            continue
        reviewed_count += 1

    click.echo(
        f"\n{'='*70}\nReview abgeschlossen: {reviewed_count} geprüft, "
        f"{len(skipped)} übersprungen, {total - reviewed_count - len(skipped)} "
        f"offen."
    )


@cli.command("batch-unklar")
@click.option("--season", "-s", required=True, help="Saison-ID (z.B. btw2025).")
@click.option("--party", "-p", required=True, help="Partei-ID.")
@click.option(
    "--flag", "-f", default="missing_evidence", show_default=True,
    help="Flag, nach dem gefiltert wird (z.B. missing_evidence).",
)
@click.option("--reviewer", "-r", help="Reviewer-Name.")
def batch_unklar(season: str, party: str, flag: str,
                 reviewer: Optional[str]) -> None:
    """Setzt alle Positionen einer Partei mit einem bestimmten Flag auf unklar.

    Standard-Anwendungsfall: alle ``missing_evidence``-Flags einer Partei
    auf ``unklar`` setzen.
    """
    db = _get_db()
    reviewer = reviewer or _prompt_reviewer()

    if flag not in KNOWN_FLAGS:
        click.echo(
            f"Warnung: '{flag}' ist kein bekanntes Standard-Flag "
            f"(bekannt: {sorted(KNOWN_FLAGS)}).",
            err=True,
        )
        if not click.confirm("Trotzdem fortfahren?", default=False):
            return

    try:
        count = db.batch_set_unklar_for_party(
            season, party, flag, reviewer,
            note=f"Batch: alle '{flag}'-Flags -> unklar",
        )
    except Exception as exc:  # noqa: BLE001
        click.echo(f"FEHLER: {exc}", err=True)
        sys.exit(1)

    if count == 0:
        click.echo(
            f"Keine Positionen mit Flag '{flag}' für Partei '{party}' "
            f"in Saison '{season}' gefunden."
        )
    else:
        click.echo(
            f"{count} Position(en) der Partei '{party}' mit Flag '{flag}' "
            f"auf 'unklar' gesetzt (solo-geprueft)."
        )


@cli.command("list-seasons")
def list_seasons() -> None:
    """Listet alle verfügbaren Saisons auf."""
    db = _get_db()
    seasons = db.list_seasons()
    if not seasons:
        click.echo("Keine Saisons gefunden.")
        return
    for s in seasons:
        click.echo(
            f"  {s['id']:20s}  {s['type']:12s}  {s['date']}  "
            f"{s['region']}  [Phase: {s['phase']}]"
        )


@cli.command("list-flagged")
@click.option("--season", "-s", required=True, help="Saison-ID.")
def list_flagged(season: str) -> None:
    """Listet alle markierten Positionen einer Saison (ohne Aktion)."""
    db = _get_db()
    flagged = db.list_flagged(season)
    if not flagged:
        click.echo(f"Keine markierten Positionen für Saison '{season}'. ✅")
        return
    for i, pos in enumerate(flagged, 1):
        _print_position(pos, i, len(flagged))
    click.echo(f"\nInsgesamt: {len(flagged)} markierte Position(en).")


@cli.command("log")
@click.argument("position_id")
def show_log(position_id: str) -> None:
    """Zeigt den Audit-Trail (review_log) für eine Position."""
    db = _get_db()
    entries = db.list_log(position_id)
    if not entries:
        click.echo(f"Keine Log-Einträge für Position '{position_id}'.")
        return
    click.echo(f"\nAudit-Trail für Position {position_id}:")
    for e in entries:
        click.echo(f"\n  [{e['created_at']}] {e['action']}  (von: {e['reviewer']})")
        if e.get("note"):
            click.echo(f"    Notiz:        {e['note']}")
        if e.get("before_state"):
            click.echo(f"    Vorher:       {e['before_state']}")
        if e.get("after_state"):
            click.echo(f"    Nachher:      {e['after_state']}")


@cli.command("freigeben")
@click.argument("position_id")
@click.option("--reviewer", "-r", help="Reviewer-Name.")
def freigeben(position_id: str, reviewer: Optional[str]) -> None:
    """Setzt eine einzelne Position auf solo-geprueft (nicht-interaktiv)."""
    db = _get_db()
    reviewer = reviewer or _prompt_reviewer()
    try:
        db.update_review_status(
            position_id, "solo-geprueft", reviewer,
            note="CLI: direkt freigegeben",
        )
        click.echo(f"Position {position_id} → solo-geprueft.")
    except ValueError as exc:
        click.echo(f"FEHLER: {exc}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
