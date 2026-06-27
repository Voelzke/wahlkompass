# Moderationsregeln — WahlKompass

Stand: 27.06.2026 · Lizenz: CC-BY-SA 4.0

Diese Regeln definieren, wie Community-Einreichungen (Issues & PRs) im
WahlKompass-Projekt moderiert werden. Sie gelten für alle Korrekturen an
Parteipositionen, Belegen und Quellenangaben.

## 1. Grundprinzipien

1. **Keine automatische Übernahme.** Jede Community-Einreichung durchläuft
   die Auto-Validierung (B.1) **und** eine menschliche Prüfung (Solo- oder
   Community-Review). Es gibt keinen „Auto-Merge".
2. **Transparenz.** Jede Entscheidung (Annahme, Änderung, Ablehnung) wird im
   `review_log` bzw. im GitHub-Issue begründet dokumentiert.
3. **Belegpflicht.** Positionskorrekturen erfordern ein wortwörtliches Zitat
   (20–300 Zeichen) mit nachvollziehbarer Quellenangabe (Seite oder URL).
3. **Gleiche Maßstäbe.** Die Regeln gelten unabhängig davon, welche Partei
   betroffen ist. Politische Bewertung findet nicht statt — es geht allein
   um die Korrektheit der Daten.

## 2. Authentifizierung

- Eine Einreichung setzt ein **GitHub-Konto** voraus. Anonyme Einreichungen
  sind nicht möglich.
- Der Account-Name (GitHub-Username) wird als Reviewer-Identität gespeichert.
- Accounts, die erst kürzlich erstellt wurden (< 7 Tage) erhalten das
  Label `new-account` und werden mit erhöhter Aufmerksamkeit geprüft.

## 3. Rate-Limit

- **Maximal 5 offene Issues pro Nutzer:in und Woche** (rollierend, 7 Tage).
  Einreichungen über dieses Limit hinaus werden automatisch mit `rate-limited`
  geschlossen und können nach Ablauf der Frist erneut eingereicht werden.
- Für PRs gilt ein separates Limit von **2 offenen Daten-PRs gleichzeitig**.

## 4. Parteikonten & Kennzeichnungspflicht

- Konten, die offiziell für eine Partei sprechen (z.B. Parteikonten,
  Wahlkampf-Teams, Angestellte), müssen dies **offen kennzeichnen** — z.B.
  im Issue-Text oder als Hinweis im GitHub-Profil.
- Als Parteikonto gekennzeichnete Einreichungen erhalten das Label
  `party-account` und durchlaufen eine **verschärfte Prüfung**:
  - Zweit-Begutachtung durch mindestens eine zweite Reviewer:in verpflichtend.
  - Höhere Anforderungen an die Quellenqualität (Bevorzugt amtliche
    Parteiprogramme / offizielle Verlautbarungen).
- Nicht-Kennzeichnung eines Parteikontos führt zum sofortigen Ausschluss der
  Einreichung (siehe §6) und kann zur Sperrung führen.

## 5. Prüfprozess für Einreichungen

Jede Einreichung durchläuft folgende Stufen:

1. **Auto-Validierung (B.1)** — automatisch, in der CI:
   - Beleg-Zitat-Länge (20–300 Zeichen).
   - Pflichtfelder vollständig (Partei, These, Position, Zitat, Quelle).
   - Positionstyp gültig (`zustimmen` / `ablehnen` / `neutral` / `unklar`).
   - Plausibilitäts-Check (z.B. Quelle nicht leer, Saison existiert).
   Schlägt die Auto-Validierung fehl, wird das Issue mit `auto-validation-failed`
   labeliert und um fehlende Informationen gebeten.

2. **Solo-Review** — eine Reviewer:in prüft die Einreichung manuell:
   - Beleg gegen das Originaldokument nachvollzogen.
   - Entscheidung: `angenommen`, `geändert` (mit eigener Korrektur) oder
     `abgelehnt` (mit Begründung).
   - Bei Parteikonten: Zweit-Begutachtung einholen.

3. **Community-Review (optional)** — bei strittigen Fällen oder Sensitiv-Rubriken
   (Migration, Innen, Demokratie) kann die Einreichung zur Community-Diskussion
   freigegeben werden (`needs-community-discussion`). Die finale Entscheidung
   trifft trotzdem das Review-Team.

## 6. Sanktionen bei missbräuchlichen Einreichungen

- **3 abgelehnte Einreichungen** (ohne später erfolgreich revidierte Version)
  → Account wird für neue Einreichungen gesperrt (`banned`).
- Offensichtlicher Missbrauch (Spam, Trollen, gezielte Desinformation,
  wiederholtes Nicht-Kennzeichnen als Parteikonto) → sofortige Sperre,
  unabhängig von der Drei-Stufen-Regel.
- Sperrungen werden im Issue begründet dokumentiert und können per Issue
  an das Moderations-Team zur Überprüfung gerichtet werden.

## 7. Datensparsamkeit

- Es werden ausschließlich GitHub-Username, Einreichungsinhalt und
  Entscheidungs-Metadaten gespeichert. Keine Tracking- oder Profildaten.
- Einreichungen unterliegen der Datenlizenz CC-BY-SA 4.0 (siehe
  [`LICENSE_DATA`](../LICENSE_DATA)).

## 8. Verantwortliche & Ansprechpartner

- Moderations-Team: @wahlkompass/moderation (über GitHub mentionbar).
- Eskalation bei Konflikten: Issue mit Label `escalation` eröffnen.

---

Bezüge: [`docs/review-prozess.md`](review-prozess.md) (Prozessablauf) ·
[`docs/methodik.md`](methodik.md) (Gesamtmethodik) ·
[`review/templates/community_correction.md`](../review/templates/community_correction.md)
(Template).
