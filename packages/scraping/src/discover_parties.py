#!/usr/bin/env python3
"""
discover_parties.py — Discover parties and create party + program entries.

Downloads election.source_url, parses the party list, and creates
party and program entries in the database with status='no_program'.

For BTW (Bundestagwahl): parses Bundeswahlleiter party list format.

Usage:
    python discover_parties.py --election-id <UUID>
    python discover_parties.py --election-id <UUID> --dry-run

The module is idempotent: running it multiple times will not create
duplicate party entries (matched by name).
"""
import argparse
import sys
import os
import re
import logging
from html.parser import HTMLParser

# Add parent dirs to path for db import
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "db"))

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class PartyListParser(HTMLParser):
    """Parse the Bundeswahlleiter party list HTML page."""

    def __init__(self):
        super().__init__()
        self.parties = []
        self._in_table = False
        self._in_row = False
        self._in_cell = False
        self._current_cell = ""
        self._current_row = []
        self._in_link = False
        self._current_link = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._in_table = True
        elif tag == "tr" and self._in_table:
            self._in_row = True
            self._current_row = []
            self._current_link = None
        elif tag in ("td", "th") and self._in_row:
            self._in_cell = True
            self._current_cell = ""
        elif tag == "a" and self._in_cell:
            self._in_link = True
            for attr, val in attrs:
                if attr == "href":
                    self._current_link = val

    def handle_endtag(self, tag):
        if tag == "table":
            self._in_table = False
        elif tag == "tr" and self._in_row:
            self._in_row = False
            if self._current_row:
                self._parse_row(self._current_row)
        elif tag in ("td", "th") and self._in_cell:
            self._in_cell = False
            self._current_row.append(self._current_cell.strip())
            self._current_cell = ""
        elif tag == "a" and self._in_link:
            self._in_link = False

    def handle_data(self, data):
        if self._in_cell:
            self._current_cell += data

    def _parse_row(self, row):
        """Parse a table row into a party dict."""
        # Bundeswahlleiter format: name, short_name, sometimes website
        # We handle flexible column counts
        if len(row) < 2:
            return
        # Skip header rows
        first = row[0].lower() if row[0] else ""
        if first in ("name", "partei", "bezeichnung", "liste"):
            return
        if not any(cell.strip() for cell in row):
            return

        name = row[0].strip() if row[0] else ""
        short_name = row[1].strip() if len(row) > 1 and row[1] else ""
        website = None
        if len(row) > 2 and row[2]:
            website = row[2].strip()
            if website and not website.startswith("http"):
                website = None

        if name:
            # Generate short name if missing
            if not short_name:
                words = name.split()
                short_name = "".join(w[0].upper() for w in words[:4])[:20]
            else:
                short_name = short_name[:20]

            self.parties.append({
                "name": name,
                "short_name": short_name,
                "website_url": website,
            })


def parse_party_list_html(html_content: str) -> list[dict]:
    """
    Parse HTML content and return list of party dicts.

    Each dict has: name, short_name, website_url (optional)
    """
    parser = PartyListParser()
    parser.feed(html_content)
    return parser.parties


def download_page(url: str) -> str:
    """Download a URL and return the HTML content."""
    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.text


def discover_parties_for_election(election_id: str, source_url: str = None,
                                   dry_run: bool = False) -> list[dict]:
    """
    Discover parties for an election.

    Args:
        election_id: UUID of the election
        source_url: URL to party list page. If None, fetch from DB.
        dry_run: If True, parse but don't write to DB

    Returns:
        List of discovered party dicts
    """
    from db.connection import get_connection

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Get election info
        if source_url is None:
            cur.execute(
                "SELECT source_url FROM election WHERE id = %s",
                (election_id,)
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Election {election_id} not found")
            source_url = row[0]

        if not source_url:
            raise ValueError(f"No source_url for election {election_id}")

        logger.info(f"Downloading party list from {source_url}")
        html_content = download_page(source_url)
        parties = parse_party_list_html(html_content)
        logger.info(f"Discovered {len(parties)} parties")

        if dry_run:
            return parties

        # Insert parties (idempotent by name)
        for party in parties:
            # Check if party already exists
            cur.execute(
                "SELECT id FROM party WHERE name = %s",
                (party["name"],)
            )
            existing = cur.fetchone()
            if existing:
                party_id = existing[0]
                logger.debug(f"Party '{party['name']}' already exists")
            else:
                cur.execute(
                    """INSERT INTO party (name, short_name, website_url)
                       VALUES (%s, %s, %s) RETURNING id""",
                    (party["name"], party["short_name"], party.get("website_url"))
                )
                party_id = cur.fetchone()[0]
                logger.info(f"Created party: {party['name']} ({party['short_name']})")

            # Create program entry with status='no_program'
            cur.execute(
                """SELECT id FROM program WHERE party_id = %s AND election_id = %s""",
                (party_id, election_id)
            )
            if not cur.fetchone():
                cur.execute(
                    """INSERT INTO program (party_id, election_id, status)
                       VALUES (%s, %s, 'no_program')""",
                    (party_id, election_id)
                )
                logger.debug(f"Created program entry for {party['name']}")

        conn.commit()
        logger.info(f"Successfully processed {len(parties)} parties")
        return parties
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Discover parties for an election"
    )
    parser.add_argument("--election-id", required=True,
                        help="UUID of the election")
    parser.add_argument("--source-url", default=None,
                        help="URL to party list (overrides election.source_url)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse but don't write to DB")

    args = parser.parse_args()

    parties = discover_parties_for_election(
        election_id=args.election_id,
        source_url=args.source_url,
        dry_run=args.dry_run,
    )

    print(f"\nDiscovered {len(parties)} parties:")
    for p in parties:
        print(f"  - {p['name']} ({p['short_name']})")
        if p.get("website_url"):
            print(f"    Website: {p['website_url']}")


if __name__ == "__main__":
    main()
