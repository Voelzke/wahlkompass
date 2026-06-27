"""
Wahlkompass FastAPI Backend — API Endpoints

Endpoints:
  GET  /api/elections                    — list elections
  GET  /api/elections/{election_id}      — get election with parties, theses, categories
  GET  /api/elections/{election_id}/theses — get theses (filtered by tier)
  GET  /api/elections/{election_id}/parties — get parties with programs
  GET  /api/positions/{election_id}       — get positions for an election
  GET  /api/evidence/{position_id}        — get evidence for a position
  POST /api/matching                       — compute matching results
  GET  /api/health                         — health check
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Wahlkompass API",
    version="0.1.0",
    description="Open-Source-Wahlkompass API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production: restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://wahlkompass:***@localhost:5432/wahlkompass",
)


def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


# ============================================================
# Models
# ============================================================

class MatchingRequest(BaseModel):
    election_id: str
    tier: str = "20"  # 20, 40, or 60plus
    answers: dict[str, str] = {}  # thesis_id → "zustimmen" | "ablehnen" | "skip"
    weights: dict[str, int] = {}  # thesis_id → 1 or 2


# ============================================================
# Position scoring constants
# ============================================================

POSITION_SCORES = {
    "zustimmen": 1,
    "ablehnen": -1,
    "neutral": 0,
    "unklar": 0,
}

USER_SCORES = {
    "zustimmen": 1,
    "ablehnen": -1,
    "skip": 0,
}

MIN_THESES_FOR_MATCHING = 5


# ============================================================
# Endpoints
# ============================================================

@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/elections")
async def list_elections():
    """List all elections."""
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT id, type, date, region, phase,
                          (SELECT count(*) FROM party p
                           JOIN program prog ON prog.party_id = p.id
                           WHERE prog.election_id = e.id AND prog.status = 'text_available') as party_count
                   FROM election e ORDER BY date DESC"""
            )
            elections = [dict(r) for r in cur.fetchall()]
        return {"elections": elections}
    finally:
        conn.close()


@app.get("/api/elections/{election_id}")
async def get_election(election_id: str):
    """Get election details with parties, categories, and thesis count."""
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Election
            cur.execute("SELECT * FROM election WHERE id = %s", (election_id,))
            election = cur.fetchone()
            if not election:
                raise HTTPException(status_code=404, detail="Election not found")
            election = dict(election)

            # Categories
            cur.execute(
                "SELECT * FROM category WHERE election_id = %s ORDER BY sort_order",
                (election_id,),
            )
            categories = [dict(r) for r in cur.fetchall()]

            # Parties
            cur.execute(
                """SELECT p.*, prog.status as program_status
                   FROM party p
                   JOIN program prog ON prog.party_id = p.id AND prog.election_id = %s
                   ORDER BY p.short_name""",
                (election_id,),
            )
            parties = [dict(r) for r in cur.fetchall()]

            # Thesis counts per tier
            cur.execute(
                """SELECT tier, count(*) as count FROM thesis
                   WHERE election_id = %s GROUP BY tier""",
                (election_id,),
            )
            thesis_counts = {r["tier"]: r["count"] for r in cur.fetchall()}

        election["categories"] = categories
        election["parties"] = parties
        election["thesis_counts"] = thesis_counts
        return election
    finally:
        conn.close()


@app.get("/api/elections/{election_id}/theses")
async def get_theses(election_id: str, tier: Optional[str] = Query(None)):
    """Get theses for an election, optionally filtered by tier."""
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if tier:
                # Get theses in tiers up to and including the requested tier
                tier_order = ["20", "40", "60plus"]
                tiers = tier_order[:tier_order.index(tier) + 1] if tier in tier_order else [tier]
                placeholders = ",".join(["%s"] * len(tiers))
                cur.execute(
                    f"""SELECT t.*, c.name as category_name, c.is_sensitive
                        FROM thesis t
                        JOIN category c ON t.category_id = c.id
                        WHERE t.election_id = %s AND t.tier IN ({placeholders})
                        ORDER BY t.tier, t.sort_order""",
                    (election_id, *tiers),
                )
            else:
                cur.execute(
                    """SELECT t.*, c.name as category_name, c.is_sensitive
                       FROM thesis t
                       JOIN category c ON t.category_id = c.id
                       WHERE t.election_id = %s
                       ORDER BY t.tier, t.sort_order""",
                    (election_id,),
                )
            theses = [dict(r) for r in cur.fetchall()]
        return {"theses": theses}
    finally:
        conn.close()


@app.get("/api/elections/{election_id}/parties")
async def get_parties(election_id: str):
    """Get parties with program status for an election."""
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT p.*, prog.status as program_status,
                          prog.source_url as program_url
                   FROM party p
                   JOIN program prog ON prog.party_id = p.id AND prog.election_id = %s
                   ORDER BY p.short_name""",
                (election_id,),
            )
            parties = [dict(r) for r in cur.fetchall()]
        return {"parties": parties}
    finally:
        conn.close()


@app.get("/api/positions/{election_id}")
async def get_positions(election_id: str, published_only: bool = True):
    """Get all positions for an election."""
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
                SELECT pos.*, t.statement, t.tier, t.category_id,
                       p.short_name as party_short_name, p.name as party_name, p.color as party_color
                FROM position pos
                JOIN thesis t ON pos.thesis_id = t.id
                JOIN party p ON pos.party_id = p.id
                WHERE t.election_id = %s
            """
            params = [election_id]
            if published_only:
                query += " AND pos.published = true"
            query += " ORDER BY p.short_name, t.tier, t.sort_order"
            cur.execute(query, params)
            positions = [dict(r) for r in cur.fetchall()]
        return {"positions": positions}
    finally:
        conn.close()


@app.get("/api/evidence/{position_id}")
async def get_evidence(position_id: str):
    """Get evidence for a specific position."""
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """SELECT ev.*, pos.position_type, pos.party_id, pos.thesis_id,
                          t.statement, p.short_name as party_short_name
                   FROM evidence ev
                   JOIN position pos ON ev.position_id = pos.id
                   JOIN thesis t ON pos.thesis_id = t.id
                   JOIN party p ON pos.party_id = p.id
                   WHERE ev.position_id = %s""",
                (position_id,),
            )
            evidence = cur.fetchone()
            if not evidence:
                raise HTTPException(status_code=404, detail="Evidence not found")
            evidence = dict(evidence)
            if isinstance(evidence.get("quote_location"), str):
                evidence["quote_location"] = json.loads(evidence["quote_location"])
        return evidence
    finally:
        conn.close()


@app.post("/api/matching")
async def compute_matching(req: MatchingRequest):
    """
    Compute matching results.

    Scoring (§A.7.3):
    - match(p, t) = s_user(t) * s_party(p, t)
    - weighted(p, t) = match(p, t) * w(t)
    - score(p) = sum of weighted(p, t)
    - norm(p) = score(p) / sum of |w(t)| for non-skipped theses
    - Min 5 theses answered
    """
    # Check minimum theses
    answered = {k: v for k, v in req.answers.items() if v != "skip"}
    if len(answered) < MIN_THESES_FOR_MATCHING:
        raise HTTPException(
            status_code=400,
            detail=f"Mindestens {MIN_THESES_FOR_MATCHING} Thesen müssen beantwortet werden.",
        )

    conn = get_db()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get tier filter
            tier_order = ["20", "40", "60plus"]
            tiers = tier_order[:tier_order.index(req.tier) + 1] if req.tier in tier_order else [req.tier]
            placeholders = ",".join(["%s"] * len(tiers))

            # Get all published positions for the election in the requested tier
            cur.execute(
                f"""SELECT pos.id, pos.party_id, pos.thesis_id, pos.position_type,
                           pos.review_status, p.short_name, p.name, p.color
                    FROM position pos
                    JOIN thesis t ON pos.thesis_id = t.id
                    JOIN party p ON pos.party_id = p.id
                    WHERE t.election_id = %s AND t.tier IN ({placeholders})
                      AND pos.published = true
                      AND pos.position_type != 'unklar'""",
                (req.election_id, *tiers),
            )
            positions = cur.fetchall()

        # Group positions by party
        party_positions = {}
        for pos in positions:
            pid = pos["party_id"]
            party_positions.setdefault(pid, {
                "party_id": pid,
                "short_name": pos["short_name"],
                "name": pos["name"],
                "color": pos["color"],
                "positions": {},
            })
            party_positions[pid]["positions"][pos["thesis_id"]] = pos["position_type"]

        # Compute scores
        results = []
        for party_id, party_data in party_positions.items():
            score = 0
            max_score = 0

            for thesis_id, user_answer in req.answers.items():
                if user_answer == "skip":
                    continue

                user_score = USER_SCORES.get(user_answer, 0)
                party_pos = party_data["positions"].get(thesis_id)
                if party_pos is None:
                    continue  # Party has no position on this thesis

                party_score = POSITION_SCORES.get(party_pos, 0)
                weight = req.weights.get(thesis_id, 1)

                match = user_score * party_score
                score += match * weight
                max_score += abs(weight)

            if max_score == 0:
                continue

            norm = score / max_score  # [-1, +1]
            percentage = round((norm + 1) / 2 * 100)  # [0, 100]

            results.append({
                "party_id": party_id,
                "short_name": party_data["short_name"],
                "name": party_data["name"],
                "color": party_data["color"],
                "score": score,
                "norm": round(norm, 4),
                "percentage": percentage,
            })

        # Sort by norm descending, then alphabetically by short_name
        results.sort(key=lambda r: (-r["norm"], r["short_name"]))

        # Assign ranks with tie handling
        ranked = []
        current_rank = 1
        prev_norm = None
        tie_count = 0

        for i, r in enumerate(results):
            if prev_norm is not None and r["norm"] == prev_norm:
                # Tie — same rank as previous
                tie_count += 1
                rank = current_rank - 1  # Wait, need to think about this
                # Actually: ties get the same rank, next non-tie gets current_rank + tie_count
                ranked.append({**r, "rank": ranked[-1]["rank"], "tied": True})
            else:
                rank = i + 1
                current_rank = rank
                tie_count = 0
                ranked.append({**r, "rank": rank, "tied": False})
            prev_norm = r["norm"]

        # Mark all in a tie group as tied
        i = 0
        while i < len(ranked):
            j = i + 1
            while j < len(ranked) and ranked[j]["norm"] == ranked[i]["norm"]:
                j += 1
            if j > i + 1:
                for k in range(i, j):
                    ranked[k]["tied"] = True
            i = j

        return {
            "results": ranked,
            "total_parties": len(ranked),
            "theses_answered": len(answered),
            "tier": req.tier,
        }
    finally:
        conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
