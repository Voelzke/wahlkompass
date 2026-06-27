"""
extract.py — KI-Extraktion von Parteipositionen aus Wahlprogramm-Texten.

Lädt Programm-Text-Chunks, sendet sie an ein Extraktions-Modell,
schreibt Positionen und Belege in die DB.
"""

import json
import os
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor

# Sensitive categories — always flagged for solo review
SENSITIVE_CATEGORIES = {
    "Migration und Integration",
    "Demokratie und Verfassung",
    "Innen und Recht",
}

VALID_POSITION_TYPES = {"zustimmen", "ablehnen", "neutral", "unklar"}


def get_db_connection():
    """Verbinde mit PostgreSQL via DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL", "postgresql://wahlkompass:wahlkompass@localhost:5432/wahlkompass")
    return psycopg2.connect(db_url)


def load_prompt() -> str:
    """Lade den Extraktions-Prompt."""
    prompt_path = Path(__file__).parent.parent / "prompts" / "extract_positions.md"
    return prompt_path.read_text(encoding="utf-8")


def load_theses(conn, election_id: str) -> list[dict]:
    """Lade alle Thesen für eine Wahl aus der DB."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT t.id, t.statement, t.tier, c.name as category_name, c.is_sensitive
            FROM thesis t
            JOIN category c ON t.category_id = c.id
            WHERE t.election_id = %s
            ORDER BY t.tier, t.sort_order
            """,
            (election_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def load_program_text(extract_path: str) -> str:
    """Lade den extrahierten Programmtext."""
    if not extract_path:
        return ""
    p = Path(extract_path)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def chunk_text(text: str, max_chars: int = 4000, overlap: int = 200) -> list[str]:
    """Zerlege Text in überlappende Chunks."""
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def call_extraction_model(prompt: str, theses: list[dict], chunk: str, model: str = "gpt-4o") -> dict:
    """
    Rufe das Extraktions-Modell auf.

    In Produktion: echter API-Call (OpenAI, Anthropic, OpenRouter).
    Für Tests: Mock-Implementation.
    """
    # In Produktion würde hier der echte API-Call stehen:
    # import openai
    # client = openai.Client()
    # response = client.chat.completions.create(
    #     model=model,
    #     messages=[
    #         {"role": "system", "content": prompt},
    #         {"role": "user", "content": json.dumps({"theses": [...], "program_chunk": chunk})}
    #     ],
    #     response_format={"type": "json_object"}
    # )
    # return json.loads(response.choices[0].message.content)

    # Mock: return empty positions for all theses
    return {
        "positions": [
            {
                "thesis_id": t["id"],
                "position_type": "unklar",
                "quote": None,
                "quote_location": None,
            }
            for t in theses
        ]
    }


def merge_positions(chunk_results: list[dict]) -> dict:
    """
    Merge Positionen aus mehreren Chunks.
    Konfliktlösung: letzter Fund gewinnt (nicht-unklar schlägt unklar).
    """
    merged = {}
    for result in chunk_results:
        for pos in result.get("positions", []):
            thesis_id = pos["thesis_id"]
            if thesis_id not in merged:
                merged[thesis_id] = pos
            elif merged[thesis_id]["position_type"] == "unklar" and pos["position_type"] != "unklar":
                merged[thesis_id] = pos
            elif pos["position_type"] != "unklar":
                merged[thesis_id] = pos
    return merged


def save_position(
    conn,
    party_id: str,
    thesis_id: str,
    program_id: str,
    position_type: str,
    quote: Optional[str],
    quote_location: Optional[dict],
    model: str,
    model_version: str,
):
    """Speichere Position + Beleg in der DB."""
    now = datetime.now(timezone.utc)
    position_id = hashlib.sha256(f"{party_id}{thesis_id}{program_id}".encode()).hexdigest()[:36]

    with conn.cursor() as cur:
        # Insert or update position
        cur.execute(
            """
            INSERT INTO position (id, party_id, thesis_id, program_id, position_type,
                                  extracted_at, extraction_model, extraction_model_version,
                                  review_status, published, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'geflaggt', false, %s, %s)
            ON CONFLICT (party_id, thesis_id) DO UPDATE
            SET position_type = EXCLUDED.position_type,
                extracted_at = EXCLUDED.extracted_at,
                extraction_model = EXCLUDED.extraction_model,
                extraction_model_version = EXCLUDED.extraction_model_version,
                updated_at = EXCLUDED.updated_at
            RETURNING id
            """,
            (position_id, party_id, thesis_id, program_id, position_type,
             now, model, model_version, now, now),
        )
        row = cur.fetchone()
        if row:
            position_id = row[0]

        # Insert evidence if position is not unklar
        if position_type != "unklar" and quote:
            evidence_id = hashlib.sha256(f"ev{position_id}".encode()).hexdigest()[:36]
            cur.execute(
                """
                INSERT INTO evidence (id, position_id, quote, quote_location, program_id,
                                       verified_by, extracted_at, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, 'auto', %s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                SET quote = EXCLUDED.quote,
                    quote_location = EXCLUDED.quote_location,
                    updated_at = EXCLUDED.updated_at
                """,
                (evidence_id, position_id, quote, json.dumps(quote_location) if quote_location else None,
                 program_id, now, now, now),
            )

        # Write to review_log
        cur.execute(
            """
            INSERT INTO review_log (id, position_id, reviewer, decision, flag_reasons,
                                      note, reviewed_at, created_at)
            VALUES (gen_random_uuid(), %s, 'auto', 'flag', ARRAY[]::text[],
                    'Position extrahiert', %s, %s)
            """,
            (position_id, now, now),
        )

    conn.commit()
    return position_id


def run_extraction(
    election_id: str,
    party_id: str,
    model: str = "gpt-4o",
    model_version: str = "2024-08-06",
    db_url: Optional[str] = None,
):
    """
    Hauptfunktion: Extrahiere Positionen für eine Partei in einer Wahl.

    1. Lade das Programm der Partei
    2. Zerlege in Chunks
    3. Sende jeden Chunk an das Modell
    4. Merge Ergebnisse
    5. Speichere in DB
    """
    os.environ.setdefault("DATABASE_URL", db_url or "")
    conn = get_db_connection()

    # Load program
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT p.id, p.text_extract_path, p.source_format, p.has_page_numbers
            FROM program p
            WHERE p.election_id = %s AND p.party_id = %s AND p.status = 'text_available'
            """,
            (election_id, party_id),
        )
        program = cur.fetchone()
        if not program:
            return {"error": "No program with text_available found", "party_id": party_id}
        program = dict(program)

    program_text = load_program_text(program["text_extract_path"])
    if not program_text:
        return {"error": "Program text not found", "path": program["text_extract_path"]}

    theses = load_theses(conn, election_id)
    prompt = load_prompt()

    chunks = chunk_text(program_text)
    chunk_results = []

    for chunk in chunks:
        result = call_extraction_model(prompt, theses, chunk, model)
        chunk_results.append(result)

    merged = merge_positions(chunk_results)

    # Save positions
    saved = 0
    for thesis_id, pos in merged.items():
        save_position(
            conn,
            party_id=party_id,
            thesis_id=thesis_id,
            program_id=program["id"],
            position_type=pos["position_type"],
            quote=pos.get("quote"),
            quote_location=pos.get("quote_location"),
            model=model,
            model_version=model_version,
        )
        saved += 1

    conn.close()
    return {
        "party_id": party_id,
        "election_id": election_id,
        "positions_extracted": saved,
        "chunks_processed": len(chunks),
    }
