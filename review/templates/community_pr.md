# PR: Direkte Daten-Korrektur

Dieser Pull Request korrigiert Parteipositionen / Belege direkt in den Datendateien unter `data/positions/`. Bitte fülle die folgenden Felder aus, damit die Reviewer die Änderung prüfen können.

> Direkte PRs sind nur für offensichtliche, gut belegte Korrekturen gedacht (z.B. Tippfehler in Zitaten, falsche Seitenangaben, fehlerhafter `position_type` mit eindeutigem Beleg). Für unsichere Positionen bitte stattdessen ein Issue mit dem [Community-Korrektur-Template](community_correction.md) öffnen.

## Zusammenfassung

- **Partei:** [...]
- **These / These-ID:** [...]
- **Saison:** [btw2025 / ...]
- **Art der Änderung:** [position_type korrigiert / Beleg-Zitat korrigiert / Beleg-Quelle ergänzt / Position entfernt / sonstiges]

## Vorher → Nachher

| Feld | Vorher | Nachher |
|------|--------|---------|
| position_type | [...] | [...] |
| beleg.quote | [...] | [...] |
| beleg.source | [...] | [...] |
| beleg.page | [...] | [...] |
| beleg.url | [...] | [...] |

## Beleg

- **Beleg-Zitat:** [...] (min 20, max 300 Zeichen, wortwörtlich)
- **Beleg-Ort:** [Seite X / URL]
- **Dokument:** [z.B. „Bundestagswahlprogramm 2025 der Partei Z"]

## Begründung

- **Begründung:** [...] (warum die Änderung korrekt ist)

## Checklist

- [ ] Die Änderung betrifft Dateien unter `data/positions/` (CC-BY-SA 4.0).
- [ ] Zitate sind wortwörtlich und 20–300 Zeichen lang.
- [ ] Beleg-Ort ist nachvollziehbar (Seitenzahl / URL).
- [ ] Auto-Validierung (B.1) läuft im CI grün.
- [ ] Ich habe die [`Moderationsregeln`](../docs/moderation.md) gelesen.
- [ ] Bei mehreren Positionen: ein Commit pro Position für bessere Reviewbarkeit.
