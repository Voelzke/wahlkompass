#!/usr/bin/env python3
"""
init_season.py — Create a new election season with seed categories.

Usage:
    python init_season.py --type bundestag --date 2025-02-23 --region Bund
    python init_season.py --type landtag --date 2026-03-14 --region Bayern \\
        --source-url https://example.de

Creates an election row and inserts the 10 standard categories.
Idempotent: if an election with the same type+date+region exists, it returns
the existing election and ensures categories are present.
"""
import argparse
import sys
import os
import uuid
from datetime import date

# Allow running as a script: add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_connection, get_database_url

STANDARD_CATEGORIES = [
    ("Wirtschaft und Finanzen",
     "Steuer-, Haushalts- und Wirtschaftspolitik, Arbeitsmarkt, öffentliche Finanzen",
     1, False),
    ("Soziales und Gesundheit",
     "Renten-, Gesundheits- und Sozialpolitik, Pflege, Arbeitslosenschutz",
     2, False),
    ("Klima und Umwelt",
     "Klimaschutz, Energiepolitik, Umweltschutz, erneuerbare Energien",
     3, False),
    ("Bildung und Forschung",
     "Bildungspolitik, Schulen, Hochschulen, Forschungsförderung, Wissenschaft",
     4, False),
    ("Europa und Außenpolitik",
     "Europäische Union, Außen- und Sicherheitspolitik, internationale Zusammenarbeit",
     5, False),
    ("Innen und Recht",
     "Innere Sicherheit, Justiz, Verbraucherschutz, Datenschutzgrundlagen",
     6, True),
    ("Migration und Integration",
     "Migrationspolitik, Asyl, Integration, Einwanderungsgesetze",
     7, True),
    ("Demokratie und Verfassung",
     "Verfassungsrecht, Demokratieförderung, Wahlsystem, politische Teilhabe",
     8, True),
    ("Verkehr und Infrastruktur",
     "Verkehrspolitik, Mobilität, digitale und physische Infrastruktur",
     9, False),
    ("Digitales und Datenschutz",
     "Digitalisierung, KI-Regulierung, IT-Sicherheit, digitale Grundrechte",
     10, False),
]


def create_season(election_type: str, election_date: str, region: str,
                  source_url: str = None, phase: str = "erfassung") -> str:
    """
    Create an election season with seed categories.

    Returns the election UUID.
    Idempotent: returns existing election if type+date+region matches.
    """
    conn = get_connection()
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # Check if election already exists (idempotent)
        cur.execute(
            """SELECT id FROM election
               WHERE type = %s AND date = %s AND region = %s""",
            (election_type, election_date, region)
        )
        row = cur.fetchone()
        if row:
            election_id = row[0]
        else:
            election_id = str(uuid.uuid4())
            cur.execute(
                """INSERT INTO election (id, type, date, region, source_url, phase)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (election_id, election_type, election_date, region, source_url, phase)
            )

        # Insert standard categories (idempotent via name+election_id uniqueness check)
        for name, description, sort_order, is_sensitive in STANDARD_CATEGORIES:
            cur.execute(
                """SELECT id FROM category
                   WHERE election_id = %s AND name = %s""",
                (election_id, name)
            )
            if not cur.fetchone():
                cat_id = str(uuid.uuid4())
                cur.execute(
                    """INSERT INTO category (id, election_id, name, description,
                       sort_order, is_sensitive)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (cat_id, election_id, name, description, sort_order, is_sensitive)
                )

        conn.commit()
        return election_id
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Create a new election season with seed categories"
    )
    parser.add_argument("--type", required=True,
                        choices=["bundestag", "landtag", "europawahl"],
                        help="Election type")
    parser.add_argument("--date", required=True,
                        help="Election date (YYYY-MM-DD)")
    parser.add_argument("--region", required=True,
                        help="Region (e.g. Bund, Bayern, Europa)")
    parser.add_argument("--source-url", default=None,
                        help="URL to official party list source")
    parser.add_argument("--phase", default="erfassung",
                        choices=["erfassung", "preview", "live", "archiv"],
                        help="Election phase (default: erfassung)")

    args = parser.parse_args()

    # Validate date
    try:
        date.fromisoformat(args.date)
    except ValueError:
        print(f"Error: Invalid date format '{args.date}'. Use YYYY-MM-DD.",
              file=sys.stderr)
        sys.exit(1)

    election_id = create_season(
        election_type=args.type,
        election_date=args.date,
        region=args.region,
        source_url=args.source_url,
        phase=args.phase,
    )
    print(f"Election season created: {election_id}")
    print(f"  Type: {args.type}")
    print(f"  Date: {args.date}")
    print(f"  Region: {args.region}")
    print(f"  Categories: {len(STANDARD_CATEGORIES)} standard categories seeded")


if __name__ == "__main__":
    main()
