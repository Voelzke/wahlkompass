#!/usr/bin/env python3
"""
download_programs.py — Download party programs and update DB.

Downloads program.source_url, saves to data/programs/<election>/<party_short>.<ext>,
sets SHA-256 checksum and fetched_at.

Usage:
    python download_programs.py --election-id <UUID>
    python download_programs.py --election-id <UUID> --party-id <UUID>
    python download_programs.py --election-id <UUID> --dry-run

Idempotent: skips programs that already have local_path set (unless --force).
"""
import argparse
import sys
import os
import hashlib
import logging
from pathlib import Path
from urllib.parse import urlparse

# Add parent dirs to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "db"))

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Project root (3 levels up from src/)
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data" / "programs"


def get_file_extension(url: str, content_type: str = None) -> str:
    """Determine file extension from URL or content-type."""
    # Try URL path first
    parsed = urlparse(url)
    path = parsed.path.lower()
    if path.endswith(".pdf"):
        return "pdf"
    elif path.endswith(".html") or path.endswith(".htm"):
        return "html"

    # Try content-type
    if content_type:
        ct = content_type.lower()
        if "pdf" in ct:
            return "pdf"
        elif "html" in ct:
            return "html"

    # Default
    return "pdf"


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_election_identifier(conn, election_id: str) -> str:
    """Get a filesystem-safe identifier for the election."""
    cur = conn.cursor()
    cur.execute(
        "SELECT type, date, region FROM election WHERE id = %s",
        (election_id,)
    )
    row = cur.fetchone()
    if not row:
        raise ValueError(f"Election {election_id} not found")
    etype, edate, region = row
    # Create slug: e.g. "bundestag_2025-02-23_bund"
    slug = f"{etype}_{edate}_{region}".lower().replace(" ", "-")
    # Remove non-alphanumeric except - and _
    slug = "".join(c for c in slug if c.isalnum() or c in "-_")
    return slug


def download_program(url: str, dest_path: Path) -> tuple[str, str]:
    """
    Download a URL to dest_path.

    Returns (checksum, content_type).
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    with httpx.Client(follow_redirects=True, timeout=120.0) as client:
        with client.stream("GET", url) as resp:
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")

            with open(dest_path, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=8192):
                    f.write(chunk)

    checksum = compute_sha256(dest_path)
    return checksum, content_type


def download_programs_for_election(election_id: str, party_id: str = None,
                                    force: bool = False, dry_run: bool = False):
    """
    Download all programs for an election.

    Args:
        election_id: UUID of the election
        party_id: If given, only download for this party
        force: Re-download even if local_path exists
        dry_run: Don't actually download
    """
    from db.connection import get_connection

    conn = get_connection()
    cur = conn.cursor()

    try:
        election_slug = get_election_identifier(conn, election_id)
        election_dir = DATA_DIR / election_slug

        # Get programs to download
        if party_id:
            cur.execute(
                """SELECT p.id, p.source_url, p.source_format, p.local_path,
                          party.short_name, party.name
                   FROM program p
                   JOIN party ON p.party_id = party.id
                   WHERE p.election_id = %s AND p.party_id = %s AND p.source_url IS NOT NULL""",
                (election_id, party_id)
            )
        else:
            cur.execute(
                """SELECT p.id, p.source_url, p.source_format, p.local_path,
                          party.short_name, party.name
                   FROM program p
                   JOIN party ON p.party_id = party.id
                   WHERE p.election_id = %s AND p.source_url IS NOT NULL""",
                (election_id,)
            )

        programs = cur.fetchall()
        logger.info(f"Found {len(programs)} programs to download")

        for prog in programs:
            prog_id, source_url, source_format, local_path, short_name, party_name = prog

            if local_path and not force:
                logger.info(f"Skipping {party_name} — already downloaded to {local_path}")
                continue

            if dry_run:
                logger.info(f"[DRY RUN] Would download {party_name}: {source_url}")
                continue

            # Determine extension
            if source_format:
                ext = source_format
            else:
                ext = "pdf"  # Will be determined after download

            safe_short = "".join(c for c in short_name if c.isalnum() or c in "-_").lower()
            dest_path = election_dir / f"{safe_short}.{ext}"

            logger.info(f"Downloading {party_name} from {source_url}")
            try:
                checksum, content_type = download_program(source_url, dest_path)

                # Re-check extension based on content type if format wasn't set
                actual_ext = get_file_extension(source_url, content_type)
                if actual_ext != ext:
                    new_path = election_dir / f"{safe_short}.{actual_ext}"
                    dest_path.rename(new_path)
                    dest_path = new_path

                # Update DB
                cur.execute(
                    """UPDATE program
                       SET source_url = %s, source_checksum = %s, local_path = %s,
                           source_format = %s, fetched_at = now(), status = 'graphical_only'
                       WHERE id = %s""",
                    (source_url, checksum, str(dest_path.relative_to(PROJECT_ROOT)),
                     actual_ext, prog_id)
                )
                conn.commit()
                logger.info(f"Downloaded {party_name} → {dest_path} (SHA-256: {checksum[:12]}...)")

            except Exception as e:
                logger.error(f"Failed to download {party_name}: {e}")
                conn.rollback()
                continue

        logger.info("Download complete")
    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Download party programs for an election"
    )
    parser.add_argument("--election-id", required=True,
                        help="UUID of the election")
    parser.add_argument("--party-id", default=None,
                        help="Only download for this party UUID")
    parser.add_argument("--force", action="store_true",
                        help="Re-download even if already downloaded")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be downloaded")

    args = parser.parse_args()

    download_programs_for_election(
        election_id=args.election_id,
        party_id=args.party_id,
        force=args.force,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
