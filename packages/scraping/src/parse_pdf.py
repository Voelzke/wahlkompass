#!/usr/bin/env python3
"""
parse_pdf.py — Extract text from PDF party programs.

Uses pdfplumber for text extraction, with OCR fallback via pytesseract.
Detects page numbers via regex. Saves plaintext to
data/extracted_text/<election>/<party_short>.txt

Usage:
    python parse_pdf.py --election-id <UUID>
    python parse_pdf.py --election-id <UUID> --party-id <UUID>
    python parse_pdf.py --file /path/to/program.pdf --output /path/to/output.txt

Idempotent: skips programs that already have text_extract_path (unless --force).
"""
import argparse
import sys
import os
import re
import logging
from pathlib import Path
from typing import Optional

# Add parent dirs to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "db"))

import pdfplumber

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = PROJECT_ROOT / "data" / "extracted_text"

# Page number detection patterns
PAGE_NUMBER_PATTERNS = [
    re.compile(r"^\s*\d+\s*$", re.MULTILINE),  # Just a number
    re.compile(r"^\s*Seite\s+\d+\s*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*S\.\s*\d+\s*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*\d+\s*/\s*\d+\s*$", re.MULTILINE),  # 1/42
]


def detect_page_number(text: str) -> bool:
    """
    Detect if a page's text contains a page number.

    Returns True if a page number pattern is found.
    """
    if not text or not text.strip():
        return False

    # Check last few lines (page numbers usually at bottom)
    lines = text.strip().split("\n")
    last_lines = lines[-5:] if len(lines) >= 5 else lines

    for line in last_lines:
        line = line.strip()
        if not line:
            continue
        for pattern in PAGE_NUMBER_PATTERNS:
            if pattern.match(line):
                return True

    # Also check first few lines (sometimes at top)
    first_lines = lines[:3] if len(lines) >= 3 else lines
    for line in first_lines:
        line = line.strip()
        if not line:
            continue
        for pattern in PAGE_NUMBER_PATTERNS:
            if pattern.match(line):
                return True

    return False


def extract_text_from_pdf(pdf_path: str) -> tuple[list[str], int, bool]:
    """
    Extract text from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Tuple of (list of page texts, page count, has_page_numbers)
    """
    pages_text = []
    page_count = 0
    has_page_numbers = False

    try:
        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)
            logger.info(f"PDF has {page_count} pages")

            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""

                # Check for page numbers
                if text and detect_page_number(text):
                    has_page_numbers = True

                # If page has very little text, try OCR
                if len(text.strip()) < 50:
                    ocr_text = ocr_page(page, pdf_path, i)
                    if ocr_text:
                        text = ocr_text

                pages_text.append(text)
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")
        raise

    return pages_text, page_count, has_page_numbers


def ocr_page(page, pdf_path: str, page_index: int) -> str:
    """
    Attempt OCR on a page using pytesseract.

    Returns extracted text or empty string.
    """
    try:
        import pytesseract
        from PIL import Image
        import io

        # Convert page to image
        im = page.to_image(resolution=200)
        img = im.original

        # Run OCR
        text = pytesseract.image_to_string(img, lang="deu+eng")
        logger.info(f"OCR extracted {len(text)} chars from page {page_index + 1}")
        return text
    except ImportError:
        logger.warning("pytesseract or PIL not available — skipping OCR")
        return ""
    except Exception as e:
        logger.warning(f"OCR failed for page {page_index + 1}: {e}")
        return ""


def parse_pdf_file(pdf_path: str, output_path: str = None) -> dict:
    """
    Parse a PDF file and save extracted text.

    Args:
        pdf_path: Path to the PDF file
        output_path: Path for output text file. If None, uses same dir.

    Returns:
        Dict with keys: text_path, page_count, has_page_numbers, pages
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if output_path is None:
        output_path = pdf_path.with_suffix(".txt")
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    pages_text, page_count, has_page_numbers = extract_text_from_pdf(str(pdf_path))

    # Write all pages to a single text file, separated by page markers
    with open(output_path, "w", encoding="utf-8") as f:
        for i, text in enumerate(pages_text):
            f.write(f"--- PAGE {i + 1} ---\n")
            f.write(text)
            f.write("\n\n")

    logger.info(f"Extracted text saved to {output_path}")

    return {
        "text_path": str(output_path),
        "page_count": page_count,
        "has_page_numbers": has_page_numbers,
        "pages": pages_text,
    }


def parse_programs_for_election(election_id: str, party_id: str = None,
                                 force: bool = False):
    """
    Parse all PDF programs for an election.

    Updates the program table with text_extract_path, page_count, has_page_numbers.
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

        # Get programs with local_path set
        if party_id:
            cur.execute(
                """SELECT p.id, p.local_path, p.text_extract_path, party.short_name
                   FROM program p
                   JOIN party ON p.party_id = party.id
                   WHERE p.election_id = %s AND p.party_id = %s
                     AND p.local_path IS NOT NULL
                     AND p.source_format = 'pdf'""",
                (election_id, party_id)
            )
        else:
            cur.execute(
                """SELECT p.id, p.local_path, p.text_extract_path, party.short_name
                   FROM program p
                   JOIN party ON p.party_id = party.id
                   WHERE p.election_id = %s
                     AND p.local_path IS NOT NULL
                     AND p.source_format = 'pdf'""",
                (election_id,)
            )

        programs = cur.fetchall()
        logger.info(f"Found {len(programs)} PDF programs to parse")

        for prog in programs:
            prog_id, local_path, text_path, short_name = prog

            if text_path and not force:
                logger.info(f"Skipping {short_name} — already parsed")
                continue

            # Resolve local path relative to project root
            pdf_path = PROJECT_ROOT / local_path
            if not pdf_path.exists():
                logger.warning(f"PDF not found: {pdf_path}")
                continue

            safe_short = "".join(c for c in short_name if c.isalnum() or c in "-_").lower()
            output_path = election_dir / f"{safe_short}.txt"

            logger.info(f"Parsing PDF for {short_name}")
            try:
                result = parse_pdf_file(str(pdf_path), str(output_path))

                cur.execute(
                    """UPDATE program
                       SET text_extract_path = %s, page_count = %s,
                           has_page_numbers = %s, status = 'text_available'
                       WHERE id = %s""",
                    (str(output_path.relative_to(PROJECT_ROOT)),
                     result["page_count"], result["has_page_numbers"], prog_id)
                )
                conn.commit()
                logger.info(f"Parsed {short_name}: {result['page_count']} pages, "
                           f"page_numbers={result['has_page_numbers']}")
            except Exception as e:
                logger.error(f"Failed to parse {short_name}: {e}")
                conn.rollback()
                continue

        logger.info("PDF parsing complete")
    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Extract text from PDF party programs"
    )
    parser.add_argument("--election-id", default=None,
                        help="UUID of the election (parse all programs)")
    parser.add_argument("--party-id", default=None,
                        help="Only parse for this party UUID")
    parser.add_argument("--file", default=None,
                        help="Parse a single PDF file directly")
    parser.add_argument("--output", default=None,
                        help="Output text file path (with --file)")
    parser.add_argument("--force", action="store_true",
                        help="Re-parse even if already parsed")

    args = parser.parse_args()

    if args.file:
        result = parse_pdf_file(args.file, args.output)
        print(f"Pages: {result['page_count']}")
        print(f"Has page numbers: {result['has_page_numbers']}")
        print(f"Output: {result['text_path']}")
    elif args.election_id:
        parse_programs_for_election(
            election_id=args.election_id,
            party_id=args.party_id,
            force=args.force,
        )
    else:
        parser.error("Either --election-id or --file is required")


if __name__ == "__main__":
    main()
