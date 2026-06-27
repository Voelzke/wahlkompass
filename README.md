# Wahlkompass

Ein Open-Source-Wahlkompass-Web-Tool nach dem Vorbild des Wahl-o-mat, aber:

1. **Live-Tool** für die jeweils nächste anstehende Wahl
2. **Wirklich alle** antretenden Parteien (BTW 2025: 41 zugelassen, 29 angetreten)
3. **Vollständig Open Source** (AGPL-3.0 Code, CC-BY-SA 4.0 Daten)

## Lizenz

- **Code**: AGPL-3.0 — siehe [LICENSE](LICENSE)
- **Daten** (Parteien, Programme, Positionen, Belege): CC-BY-SA 4.0 — siehe [LICENSE_DATA](LICENSE_DATA)
- **Methodik & Dokumentation**: CC-BY-SA 4.0

## Setup

### Voraussetzungen

- Python 3.12+
- Node.js 20+
- PostgreSQL 16+ (oder Docker)

### Mit Docker

```bash
docker-compose up -d
```

Das startet PostgreSQL, die API (FastAPI, Port 8000) und das Web-Frontend (Next.js, Port 3000).

### Manuell

```bash
# Datenbank
createdb wahlkompass
psql wahlkompass -f packages/db/schema.sql
psql wahlkompass -f packages/db/seed.sql

# API
cd apps/api
pip install -e .
uvicorn src.main:app --reload --port 8000

# Web
cd apps/web
npm install
npm run dev
```

## Projektstruktur

```
wahlkompass/
├── apps/web/          # Next.js Frontend (Matching, UI)
├── apps/api/          # FastAPI Backend
├── packages/db/       # Schema, Migrationen, Seeds
├── packages/scraping/ # Parteien-Discovery, PDF/HTML-Parsing
├── packages/extraction/ # KI-Extraktion, Auto-Validierung
├── data/              # Programme, Extrakte, Positionen (CC-BY-SA)
├── docs/              # Methodik, Review-Prozess
└── review/            # Review-CLI, Community-Templates
```

## Tests

```bash
# Python
pytest packages/db/tests/ packages/scraping/tests/ packages/extraction/tests/ -v

# Web
cd apps/web && npm test
```

## Beitragen

Siehe [CONTRIBUTING.md](CONTRIBUTING.md).

## Methodik

Die vollständige Methodik-Dokumentation liegt unter [docs/methodik.md](docs/methodik.md).
