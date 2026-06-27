# Review-Modul (AP5)

Interaktives CLI für die Solo-Prüfung markierter Parteipositionen und
Community-Templates für Korrekturen.

## Schnellstart

```bash
# Abhängigkeiten installieren
pip install -r review/requirements.txt

# Datenbank-URL setzen
export DATABASE_URL="postgresql://wahlkompass:***@localhost:5432/wahlkompass"

# (Optional) Schema für Review-Tabellen anlegen
psql "$DATABASE_URL" -f review/schema_review.sql

# Reviewer-Name setzen (für Audit-Trail)
export REVIEWER="max-mustermann"

# Interaktiven Review starten
python -m review.cli review

# Direkt für eine Saison
python -m review.cli review --season btw2025
```

## Befehle

| Befehl | Beschreibung |
|--------|--------------|
| `review` | Interaktiver Review-Loop über alle markierten Positionen. |
| `list-seasons` | Listet alle Saisons. |
| `list-flagged -s SEASON` | Listet markierte Positionen (ohne Aktion). |
| `batch-unklar -s SEASON -p PARTY [-f FLAG]` | Setzt alle Positionen einer Partei mit Flag auf unklar. |
| `log POSITION_ID` | Zeigt den Audit-Trail einer Position. |
| `freigeben POSITION_ID` | Setzt eine Position direkt auf solo-geprueft. |

## Aktionen im Review-Loop

* **[1] Freigeben** — `review_status` → `solo-geprueft`
* **[2] Korrigieren** — Beleg (Zitat + Quelle) editieren, optional `position_type`, dann `solo-geprueft`
* **[3] Auf unklar setzen** — `position_type` → `unklar`, `review_status` → `solo-geprueft`
* **[4] Zurueck an KI-Extraktion** — `review_status` → `re-extraction`
* **[s] Überspringen** — ohne Aktion zur nächsten
* **[q] Beenden** — Review abbrechen

Jede Entscheidung wird mit Reviewer, Aktion, Vorher-/Nachher-Zustand und
Zeitstempel in die `review_log`-Tabelle geschrieben (Audit-Trail).

## Schema

Die erwarteten Tabellen sind in [`schema_review.sql`](schema_review.sql)
definiert (`position`, `beleg`, `review_log`, etc.). Siehe auch
[`docs/review-prozess.md`](../docs/review-prozess.md) für den Prozess und
[`docs/moderation.md`](../docs/moderation.md) für die Moderationsregeln.

## Tests

```bash
pip install pytest
pytest review/tests/ -v
```

Die Tests verwenden `unittest.mock` und benötigen keine echte Datenbank.
