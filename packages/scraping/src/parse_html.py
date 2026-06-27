#!/usr/bin/env python3
"""
parse_html.py — Extract text from HTML party programs.

Uses httpx for fetching, with Playwright fallback for JS-rendered pages.
Extracts visible text via BeautifulSoup4 and stores CSS selector paths
per paragraph.

Usage:
    python parse_html.py --election-id <UUID>
    python parse_html.py --election-id <UUID> --party-id <UUID>
    python parse_html.py --url https://example.com/program --output output.txt

Idempotent: skips programs that already have text_extract_path (unless --force).
"""
import argparse
import sys
import os
import json
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict

# Add parent dirs to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "db"))

import httpx
from bs4 import BeautifulSoup, Tag

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data" / "extracted_text"

# Tags that contain visible text content
CONTENT_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "td",
                "div", "span", "blockquote", "article", "section", "main"}

# Tags to skip entirely
SKIP_TAGS = {"script", "style", "noscript", "head", "nav", "footer",
             "aside", "form", "button", "iframe", "svg"}


@dataclass
class Paragraph:
    """A extracted paragraph with its CSS selector path."""
    text: str
    css_path: str
    tag: str
    index: int


def fetch_html(url: str, use_playwright: bool = False) -> str:
    """
    Fetch HTML content from a URL.

    Uses httpx first, falls back to Playwright for JS-rendered pages.
    """
    if not use_playwright:
        try:
            with httpx.Client(follow_redirects=True, timeout=30.0) as client:
                resp = client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; WahlkompassBot/1.0)"
                })
                resp.raise_for_status()
                return resp.text
        except httpx.HTTPError as e:
            logger.warning(f"httpx failed for {url}: {e}, trying Playwright")
            use_playwright = True

    if use_playwright:
        return fetch_with_playwright(url)

    raise RuntimeError(f"Could not fetch {url}")


def fetch_with_playwright(url: str) -> str:
    """Fetch JS-rendered page using Playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(
            "Playwright is required for JS-rendered pages but not installed. "
            "Install with: pip install playwright && playwright install chromium"
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=30000)
        html = page.content()
        browser.close()
        return html


def build_css_path(element: Tag) -> str:
    """Build a CSS selector path for an element."""
    path = []
    current = element

    while current and current.name:
        # Build selector for this element
        selector = current.name

        # Add ID if present
        if current.get("id"):
            selector += f"#{current['id']}"
            path.append(selector)
            break  # ID is unique, stop here

        # Add classes
        classes = current.get("class", [])
        if classes:
            selector += "." + ".".join(classes)

        # Add nth-of-type
        parent = current.parent
        if parent:
            siblings = [s for s in parent.children if isinstance(s, Tag) and s.name == current.name]
            if len(siblings) > 1:
                index = siblings.index(current) + 1
                selector += f":nth-of-type({index})"

        path.append(selector)
        current = parent

    return " > ".join(reversed(path))


def extract_paragraphs(html: str) -> list[Paragraph]:
    """
    Extract visible text paragraphs from HTML.

    Returns list of Paragraph objects with CSS selector paths.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted tags
    for tag in soup.find_all(SKIP_TAGS):
        tag.decompose()

    paragraphs = []
    seen_texts = set()
    idx = 0

    for element in soup.find_all(CONTENT_TAGS):
        # Get direct text (not from children that are also content tags)
        text = element.get_text(separator=" ", strip=True)

        # Skip empty or very short text
        if not text or len(text) < 3:
            continue

        # Skip if text is mostly whitespace
        if text.isspace():
            continue

        # Deduplicate: skip if this exact text was already seen
        # (common with nested divs)
        if text in seen_texts:
            continue
        seen_texts.add(text)

        css_path = build_css_path(element)
        paragraphs.append(Paragraph(
            text=text,
            css_path=css_path,
            tag=element.name,
            index=idx,
        ))
        idx += 1

    return paragraphs


def parse_html_content(html: str, output_path: str = None,
                       output_json: str = None) -> dict:
    """
    Parse HTML content and optionally save to files.

    Args:
        html: HTML string
        output_path: Path for plaintext output
        output_json: Path for JSON output (with CSS paths)

    Returns:
        Dict with paragraphs, text, paths
    """
    paragraphs = extract_paragraphs(html)

    # Build plaintext
    lines = []
    for p in paragraphs:
        lines.append(p.text)
    text = "\n\n".join(lines)

    result = {
        "text": text,
        "paragraphs": [asdict(p) for p in paragraphs],
        "paragraph_count": len(paragraphs),
    }

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        result["text_path"] = str(output_path)

    if output_json:
        output_json = Path(output_json)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        result["json_path"] = str(output_json)

    return result


def parse_programs_for_election(election_id: str, party_id: str = None,
                                 force: bool = False):
    """
    Parse all HTML programs for an election.
    """
    from db.connection import get_connection

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Get election slug
        cur.execute("SELECT type, date, region FROM election WHERE id = %s", (election_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Election {election_id} not found")
        etype, edate, region = row
        election_slug = f"{etype}_{edate}_{region}".lower().replace(" ", "")
        election_slug = "".join(c for c in election_slug if c.isalnum() or c in "-_")

        election_dir = DATA_DIR / election_slug

        if party_id:
            cur.execute(
                """SELECT p.id, p.source_url, p.text_extract_path, party.short_name
                   FROM program p
                   JOIN party ON p.party_id = party.id
                   WHERE p.election_id = %s AND p.party_id = %s
                     AND p.source_url IS NOT NULL
                     AND p.source_format = 'html'""",
                (election_id, party_id)
            )
        else:
            cur.execute(
                """SELECT p.id, p.source_url, p.text_extract_path, party.short_name
                   FROM program p
                   JOIN party ON p.party_id = party.id
                   WHERE p.election_id = %s
                     AND p.source_url IS NOT NULL
                     AND p.source_format = 'html'""",
                (election_id,)
            )

        programs = cur.fetchall()
        logger.info(f"Found {len(programs)} HTML programs to parse")

        for prog in programs:
            prog_id, source_url, text_path, short_name = prog

            if text_path and not force:
                logger.info(f"Skipping {short_name} — already parsed")
                continue

            safe_short = "".join(c for c in short_name if c.isalnum() or c in "-_").lower()
            output_path = election_dir / f"{safe_short}.txt"
            json_path = election_dir / f"{safe_short}.json"

            logger.info(f"Parsing HTML for {short_name}: {source_url}")
            try:
                html = fetch_html(source_url)
                result = parse_html_content(html, str(output_path), str(json_path))

                cur.execute(
                    """UPDATE program
                       SET text_extract_path = %s, status = 'text_available'
                       WHERE id = %s""",
                    (str(output_path.relative_to(PROJECT_ROOT)), prog_id)
                )
                conn.commit()
                logger.info(f"Parsed {short_name}: {result['paragraph_count']} paragraphs")
            except Exception as e:
                logger.error(f"Failed to parse {short_name}: {e}")
                conn.rollback()
                continue

        logger.info("HTML parsing complete")
    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Extract text from HTML party programs"
    )
    parser.add_argument("--election-id", default=None,
                        help="UUID of the election")
    parser.add_argument("--party-id", default=None,
                        help="Only parse for this party UUID")
    parser.add_argument("--url", default=None,
                        help="Parse a single URL directly")
    parser.add_argument("--output", default=None,
                        help="Output text file path (with --url)")
    parser.add_argument("--output-json", default=None,
                        help="Output JSON file path (with --url)")
    parser.add_argument("--force", action="store_true",
                        help="Re-parse even if already parsed")

    args = parser.parse_args()

    if args.url:
        html = fetch_html(args.url)
        result = parse_html_content(html, args.output, args.output_json)
        print(f"Paragraphs: {result['paragraph_count']}")
        if args.output:
            print(f"Text output: {args.output}")
        if args.output_json:
            print(f"JSON output: {args.output_json}")
    elif args.election_id:
        parse_programs_for_election(
            election_id=args.election_id,
            party_id=args.party_id,
            force=args.force,
        )
    else:
        parser.error("Either --election-id or --url is required")


if __name__ == "__main__":
    main()
