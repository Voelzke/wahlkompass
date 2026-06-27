# CONTRIBUTING — Wahlkompass

Danke, dass du beitragen möchtest! Wahlkompass ist ein Open-Source-Projekt (AGPL-3.0 / CC-BY-SA 4.0).

## Schnellstart

```bash
git clone <repo-url>
cd wahlkompass
docker-compose up -d  # startet DB, API, Web
```

## Code-Beiträge

1. Fork das Repo, erstelle einen Branch (`feature/...` oder `fix/...`)
2. Schreibe Tests für neue Funktionalität
3. Stelle sicher, dass alle Tests grün sind:
   ```bash
   pytest packages/*/tests/ -v
   cd apps/web && npm test
   ```
4. Erstelle einen Pull Request gegen `main`

## Daten-Beiträge (Community-Korrekturen)

Siehe [docs/review-prozess.md](docs/review-prozess.md) für den Community-Korrektur-Workflow.

Korrekturen an Parteipositionen werden als GitHub Issue (Template: `.github/ISSUE_TEMPLATE/community_correction.md`) oder PR eingereicht.

## Code-Style

- **Python**: Black-Formatierung, Type Hints wo möglich
- **TypeScript**: ESLint + Prettier
- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`)

## Lizenz

Durch das Einreichen von Beiträgen stimmst du zu, dass diese unter AGPL-3.0 (Code) bzw. CC-BY-SA 4.0 (Daten) lizenziert werden.
