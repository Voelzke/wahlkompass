"""Datenbank-Zugriffsschicht für das Review-CLI (AP5).

Kapselt alle SQL-Zugriffe hinter der Klasse ``ReviewDB``, sodass das CLI
(:mod:`review.cli`) und die Tests (:mod:`review.tests.test_cli`) sauber
gegen eine klar definierte Schnittstelle arbeiten. Die Tests verwenden
``unittest.mock`` — es wird keine echte Datenbank benötigt.

Schema
------
Die erwarteten Tabellen sind in ``review/schema_review.sql`` definiert.
Kurzfassung der relevanten Tabellen:

* ``position`` — Parteiposition mit ``position_type`` (zustimmen/ablehnen/
  neutral/unklar), ``review_status`` (pending/solo-geprueft/re-extraction/
  community-geprueft) und ``flags`` (JSONB-Array von Flag-Gründen).
* ``beleg`` — Zitat + Quelle pro Position.
* ``review_log`` — Audit-Trail jeder Review-Entscheidung.

Die Verbindung erfolgt über die Umgebungsvariable ``DATABASE_URL``
(PostgreSQL-Connection-String, z.B.
``postgresql://wahlkompass:wahlkompass@localhost:5432/wahlkompass``).
"""

from __future__ import annotations

import json
import os
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:  # pragma: no cover - psycopg2 ist Runtime-Abhängigkeit
    psycopg2 = None  # type: ignore[assignment]
    RealDictCursor = None  # type: ignore[assignment]


# --------------------------------------------------------------------------- #
# Konstanten / Enums
# --------------------------------------------------------------------------- #

VALID_POSITION_TYPES = {"zustimmen", "ablehnen", "neutral", "unklar"}
VALID_REVIEW_STATUSES = {
    "pending",
    "solo-geprueft",
    "re-extraction",
    "community-geprueft",
}

#: Mögliche Flag-Gründe (nicht abschließend — das Schema erlaubt beliebige
#: Strings, aber das CLI kennt diese Standard-Flags).
KNOWN_FLAGS = {
    "missing_evidence",
    "low_confidence",
    "short_quote",
    "ambiguous_position",
    "source_mismatch",
    "unresolved_quote",
}


# --------------------------------------------------------------------------- #
# Datenklassen
# --------------------------------------------------------------------------- #


@dataclass
class FlaggedPosition:
    """Repräsentation einer markierten Position für die Anzeige im CLI."""

    id: str
    party_name: str
    thesis_statement: str
    position_type: str
    review_status: str
    flags: list[str] = field(default_factory=list)
    beleg_quote: Optional[str] = None
    beleg_source: Optional[str] = None
    beleg_page: Optional[str] = None
    beleg_url: Optional[str] = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "FlaggedPosition":
        flags = row.get("flags")
        if isinstance(flags, str):
            try:
                flags = json.loads(flags)
            except (json.JSONDecodeError, TypeError):
                flags = []
        if flags is None:
            flags = []
        return cls(
            id=row["id"],
            party_name=row["party_name"],
            thesis_statement=row["thesis_statement"],
            position_type=row["position_type"],
            review_status=row["review_status"],
            flags=list(flags),
            beleg_quote=row.get("beleg_quote"),
            beleg_source=row.get("beleg_source"),
            beleg_page=row.get("beleg_page"),
            beleg_url=row.get("beleg_url"),
        )


# --------------------------------------------------------------------------- #
# Datenbank-Klasse
# --------------------------------------------------------------------------- #


class ReviewDB:
    """Alle Datenbankoperationen für das Review-CLI.

    Parameter
    ---------
    database_url:
        PostgreSQL-Connection-String. Wenn ``None``, wird ``DATABASE_URL``
        aus der Umgebung gelesen.
    """

    def __init__(self, database_url: Optional[str] = None) -> None:
        self.database_url = database_url or os.environ.get("DATABASE_URL")
        if not self.database_url:
            raise RuntimeError(
                "DATABASE_URL ist nicht gesetzt. Bitte die Umgebungsvariable "
                "DATABASE_URL setzen (z.B. "
                "postgresql://wahlkompass:wahlkompass@localhost:5432/wahlkompass)."
            )

    # -- Connection-Handling ------------------------------------------------ #

    @contextmanager
    def connect(self) -> Iterator[Any]:
        """Öffnet eine Verbindung und sorgt für Commit/Rollback.

        Wird als Context-Manager verwendet::

            with db.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
        """
        if psycopg2 is None:
            raise RuntimeError(
                "psycopg2 ist nicht installiert. Bitte mit "
                "`pip install psycopg2-binary` installieren."
            )
        conn = psycopg2.connect(self.database_url)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # -- Lesezugriffe ------------------------------------------------------- #

    def list_seasons(self) -> list[dict[str, Any]]:
        """Gibt alle Saisons (Wahlen) zurück, sortiert nach Datum."""
        with self.connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, type, date, region, phase "
                    "FROM election ORDER BY date DESC"
                )
                return [dict(r) for r in cur.fetchall()]

    def list_parties(self, season_id: str) -> list[dict[str, Any]]:
        """Gibt alle Parteien einer Saison zurück."""
        with self.connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, name, short_name "
                    "FROM party WHERE election_id = %s ORDER BY name",
                    (season_id,),
                )
                return [dict(r) for r in cur.fetchall()]

    def list_flagged(self, season_id: str) -> list[FlaggedPosition]:
        """Listet alle markierten Positionen einer Saison.

        Eine Position gilt als „markiert", wenn ihr ``flags``-Array nicht
        leer ist oder ihr ``review_status`` auf ``pending`` steht.
        """
        with self.connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        p.id,
                        p.position_type,
                        p.review_status,
                        p.flags,
                        py.name   AS party_name,
                        t.statement AS thesis_statement,
                        b.quote    AS beleg_quote,
                        b.source   AS beleg_source,
                        b.page     AS beleg_page,
                        b.url      AS beleg_url
                    FROM position p
                    JOIN party py  ON py.id = p.party_id
                    JOIN thesis t  ON t.id  = p.thesis_id
                    LEFT JOIN beleg b ON b.position_id = p.id
                    WHERE p.election_id = %s
                      AND (
                          (p.flags IS NOT NULL
                           AND jsonb_array_length(p.flags) > 0)
                          OR p.review_status = 'pending'
                      )
                    ORDER BY py.name, t.statement
                    """,
                    (season_id,),
                )
                rows = cur.fetchall()
        return [FlaggedPosition.from_row(dict(r)) for r in rows]

    def get_position(self, position_id: str) -> Optional[FlaggedPosition]:
        """Gibt eine einzelne Position zurück oder ``None``."""
        with self.connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        p.id,
                        p.position_type,
                        p.review_status,
                        p.flags,
                        py.name   AS party_name,
                        t.statement AS thesis_statement,
                        b.quote    AS beleg_quote,
                        b.source   AS beleg_source,
                        b.page     AS beleg_page,
                        b.url      AS beleg_url
                    FROM position p
                    JOIN party py  ON py.id = p.party_id
                    JOIN thesis t  ON t.id  = p.thesis_id
                    LEFT JOIN beleg b ON b.position_id = p.id
                    WHERE p.id = %s
                    """,
                    (position_id,),
                )
                row = cur.fetchone()
        return FlaggedPosition.from_row(dict(row)) if row else None

    def get_flagged_count(self, season_id: str) -> int:
        """Anzahl markierter Positionen (für Fortschrittsanzeige)."""
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) FROM position
                    WHERE election_id = %s
                      AND (
                          (flags IS NOT NULL
                           AND jsonb_array_length(flags) > 0)
                          OR review_status = 'pending'
                      )
                    """,
                    (season_id,),
                )
                return int(cur.fetchone()[0])

    # -- Schreibzugriffe ---------------------------------------------------- #

    def _current_state(self, conn: Any, position_id: str) -> dict[str, Any]:
        """Liest den aktuellen Zustand einer Position (für das Audit-Log)."""
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, position_type, review_status, flags "
                "FROM position WHERE id = %s",
                (position_id,),
            )
            row = cur.fetchone()
        return dict(row) if row else {}

    def update_review_status(
        self,
        position_id: str,
        review_status: str,
        reviewer: str,
        note: Optional[str] = None,
    ) -> None:
        """Setzt den ``review_status`` einer Position und schreibt ins Log."""
        if review_status not in VALID_REVIEW_STATUSES:
            raise ValueError(
                f"Ungültiger review_status '{review_status}'. "
                f"Erlaubt: {sorted(VALID_REVIEW_STATUSES)}"
            )
        with self.connect() as conn:
            before = self._current_state(conn, position_id)
            if not before:
                raise ValueError(f"Position {position_id} nicht gefunden.")
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE position SET review_status = %s, updated_at = NOW() "
                    "WHERE id = %s",
                    (review_status, position_id),
                )
            after = self._current_state(conn, position_id)
            self._write_log(conn, position_id, "freigeben" if review_status == "solo-geprueft" else "status_change",
                            reviewer, note, before, after)

    def set_position_type(
        self,
        position_id: str,
        position_type: str,
        reviewer: str,
        note: Optional[str] = None,
    ) -> None:
        """Setzt ``position_type`` (z.B. auf 'unklar') und loggt die Änderung.

        Setzt zusätzlich ``review_status`` auf 'solo-geprueft', da die
        Position durch die manuelle Entscheidung als geprüft gilt.
        """
        if position_type not in VALID_POSITION_TYPES:
            raise ValueError(
                f"Ungültiger position_type '{position_type}'. "
                f"Erlaubt: {sorted(VALID_POSITION_TYPES)}"
            )
        with self.connect() as conn:
            before = self._current_state(conn, position_id)
            if not before:
                raise ValueError(f"Position {position_id} nicht gefunden.")
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE position "
                    "SET position_type = %s, review_status = 'solo-geprueft', "
                    "    updated_at = NOW() "
                    "WHERE id = %s",
                    (position_type, position_id),
                )
            after = self._current_state(conn, position_id)
            self._write_log(
                conn, position_id, "set_unklar" if position_type == "unklar" else "position_type_change",
                reviewer, note, before, after,
            )

    def mark_for_reextraction(
        self,
        position_id: str,
        reviewer: str,
        note: Optional[str] = None,
    ) -> None:
        """Markiert eine Position für erneute KI-Extraktion."""
        with self.connect() as conn:
            before = self._current_state(conn, position_id)
            if not before:
                raise ValueError(f"Position {position_id} nicht gefunden.")
            # Flags um 're-extraction-requested' erweitern
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE position
                    SET review_status = 're-extraction',
                        flags = flags || '"re-extraction-requested"'::jsonb,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (position_id,),
                )
            after = self._current_state(conn, position_id)
            self._write_log(
                conn, position_id, "reextraction", reviewer, note, before, after,
            )

    def update_beleg(
        self,
        position_id: str,
        quote: str,
        source: str,
        page: Optional[str],
        url: Optional[str],
        reviewer: str,
        note: Optional[str] = None,
    ) -> None:
        """Aktualisiert den Beleg (Zitat + Quelle) einer Position.

        Legt einen neuen Beleg an, falls keiner existiert, und validiert
        die Zitat-Länge (min. 20, max. 300 Zeichen).
        """
        if len(quote) < 20:
            raise ValueError(
                f"Beleg-Zitat zu kurz: {len(quote)} Zeichen (min. 20)."
            )
        if len(quote) > 300:
            raise ValueError(
                f"Beleg-Zitat zu lang: {len(quote)} Zeichen (max. 300)."
            )
        if not source.strip():
            raise ValueError("Beleg-Quelle darf nicht leer sein.")
        with self.connect() as conn:
            before = self._current_state(conn, position_id)
            if not before:
                raise ValueError(f"Position {position_id} nicht gefunden.")
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM beleg WHERE position_id = %s", (position_id,)
                )
                existing = cur.fetchone()
                if existing:
                    cur.execute(
                        "UPDATE beleg "
                        "SET quote = %s, source = %s, page = %s, url = %s, "
                        "    updated_at = NOW() "
                        "WHERE position_id = %s",
                        (quote, source, page, url, position_id),
                    )
                else:
                    cur.execute(
                        "INSERT INTO beleg (id, position_id, quote, source, page, url) "
                        "VALUES (%s, %s, %s, %s, %s, %s)",
                        (f"beleg-{uuid.uuid4().hex[:12]}",
                         position_id, quote, source, page, url),
                    )
                cur.execute(
                    "UPDATE position SET review_status = 'solo-geprueft', "
                    "updated_at = NOW() WHERE id = %s",
                    (position_id,),
                )
            after = self._current_state(conn, position_id)
            self._write_log(
                conn, position_id, "korrigieren", reviewer, note, before, after,
            )

    def batch_set_unklar_for_party(
        self,
        season_id: str,
        party_id: str,
        flag: str,
        reviewer: str,
        note: Optional[str] = None,
    ) -> int:
        """Setzt alle Positionen einer Partei mit bestimmtem Flag auf 'unklar'.

        Standard-Anwendungsfall: alle ``missing_evidence``-Flags einer Partei
        auf ``unklar`` setzen. Gibt die Anzahl geänderter Positionen zurück.
        """
        with self.connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, position_type, review_status, flags
                    FROM position
                    WHERE election_id = %s AND party_id = %s
                      AND flags @> %s::jsonb
                    """,
                    (season_id, party_id, json.dumps([flag])),
                )
                rows = [dict(r) for r in cur.fetchall()]
            if not rows:
                return 0
            for row in rows:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE position "
                        "SET position_type = 'unklar', "
                        "    review_status = 'solo-geprueft', updated_at = NOW() "
                        "WHERE id = %s",
                        (row["id"],),
                    )
                self._write_log(
                    conn,
                    row["id"],
                    "batch_set_unklar",
                    reviewer,
                    note or f"Batch: Flag '{flag}' -> unklar",
                    row,
                    {**row, "position_type": "unklar",
                     "review_status": "solo-geprueft"},
                )
            return len(rows)

    # -- Audit-Log ----------------------------------------------------------- #

    def _write_log(
        self,
        conn: Any,
        position_id: str,
        action: str,
        reviewer: str,
        note: Optional[str],
        before_state: dict[str, Any],
        after_state: dict[str, Any],
    ) -> None:
        """Schreibt einen Eintrag ins review_log (Audit-Trail)."""
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO review_log
                    (id, position_id, action, reviewer, note,
                     before_state, after_state)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    f"log-{uuid.uuid4().hex[:12]}",
                    position_id,
                    action,
                    reviewer,
                    note,
                    json.dumps(before_state, default=str),
                    json.dumps(after_state, default=str),
                ),
            )

    def list_log(self, position_id: str) -> list[dict[str, Any]]:
        """Gibt den Audit-Trail für eine Position zurück."""
        with self.connect() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, action, reviewer, note, "
                    "before_state, after_state, created_at "
                    "FROM review_log WHERE position_id = %s "
                    "ORDER BY created_at DESC",
                    (position_id,),
                )
                return [dict(r) for r in cur.fetchall()]
