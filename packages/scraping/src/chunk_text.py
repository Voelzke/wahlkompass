#!/usr/bin/env python3
"""
chunk_text.py — Split plaintext into chunks for AI processing.

Splits text into chunks with a maximum character count and overlap.
Chunks are split at paragraph boundaries when possible for coherence.

Usage:
    python chunk_text.py --input text.txt --output chunks.json
    python chunk_text.py --text "..." --max-chars 4000 --overlap 200

As a library:
    from chunk_text import chunk_text
    chunks = chunk_text(text, max_chars=4000, overlap=200)
"""
import argparse
import sys
import os
import json
import logging
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_MAX_CHARS = 4000
DEFAULT_OVERLAP = 200


def chunk_text(text: str, max_chars: int = DEFAULT_MAX_CHARS,
               overlap: int = DEFAULT_OVERLAP) -> list[dict]:
    """
    Split text into chunks of at most max_chars characters.

    Uses paragraph boundaries (\n\n) when possible to avoid splitting
    mid-paragraph. Each chunk includes up to `overlap` characters of
    the previous chunk for context continuity.

    Args:
        text: The input text to chunk
        max_chars: Maximum characters per chunk (default: 4000)
        overlap: Number of characters to overlap between chunks (default: 200)

    Returns:
        List of dicts with keys: text, index, char_count, start_char, end_char
    """
    if not text or not text.strip():
        return []

    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= max_chars:
        raise ValueError("overlap must be less than max_chars")

    # Split into paragraphs
    paragraphs = text.split("\n\n")
    paragraphs = [p for p in paragraphs if p.strip()]

    # If no paragraph breaks, split by lines
    if len(paragraphs) <= 1:
        lines = text.split("\n")
        lines = [l for l in lines if l.strip()]
        if len(lines) > 1:
            paragraphs = lines

    # If still just one block, split by sentences
    if len(paragraphs) <= 1:
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s for s in sentences if s.strip()]
        if len(sentences) > 1:
            paragraphs = sentences

    chunks = []
    current_chunk = ""
    current_start = 0
    chunk_start = 0
    overlap_text = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # If adding this paragraph would exceed max_chars
        separator = "\n\n" if current_chunk else ""
        candidate = current_chunk + separator + para if current_chunk else para

        if len(candidate) > max_chars:
            # If current chunk is non-empty, save it
            if current_chunk:
                chunk_end = chunk_start + len(current_chunk)
                chunks.append({
                    "text": current_chunk,
                    "index": len(chunks),
                    "char_count": len(current_chunk),
                    "start_char": chunk_start,
                    "end_char": chunk_end,
                })

                # Prepare overlap: take last `overlap` chars of current chunk
                if overlap > 0 and len(current_chunk) > overlap:
                    overlap_text = current_chunk[-overlap:]
                else:
                    overlap_text = current_chunk if overlap > 0 else ""

                # Start new chunk with overlap
                chunk_start = chunk_end - len(overlap_text) if overlap_text else chunk_end
                current_chunk = overlap_text + separator + para if overlap_text else para
            else:
                # Single paragraph exceeds max_chars — hard split
                if len(para) > max_chars:
                    sub_chunks = split_long_text(para, max_chars, overlap)
                    for sc in sub_chunks:
                        chunks.append({
                            "text": sc["text"],
                            "index": len(chunks),
                            "char_count": len(sc["text"]),
                            "start_char": chunk_start + sc["start"],
                            "end_char": chunk_start + sc["end"],
                        })
                    chunk_start += len(para)
                    current_chunk = ""
                    overlap_text = ""
                else:
                    current_chunk = para
        else:
            current_chunk = candidate

    # Don't forget the last chunk
    if current_chunk:
        chunk_end = chunk_start + len(current_chunk)
        chunks.append({
            "text": current_chunk,
            "index": len(chunks),
            "char_count": len(current_chunk),
            "start_char": chunk_start,
            "end_char": chunk_end,
        })

    logger.info(f"Split text into {len(chunks)} chunks "
                f"(max_chars={max_chars}, overlap={overlap})")
    return chunks


def split_long_text(text: str, max_chars: int, overlap: int) -> list[dict]:
    """
    Hard-split a text that exceeds max_chars with no good paragraph boundaries.

    Returns list of dicts with: text, start, end
    """
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + max_chars, len(text))

        # Try to split at word boundary
        if end < len(text):
            # Look back for a space
            space_pos = text.rfind(" ", start, end)
            if space_pos > start + max_chars // 2:
                end = space_pos

        chunk = text[start:end].strip()
        if chunk:
            chunks.append({"text": chunk, "start": start, "end": end})

        # Move start with overlap
        if end >= len(text):
            break
        start = end - overlap if overlap > 0 else end
        if start <= chunks[-1]["start"]:
            start = end

    return chunks


def chunk_file(input_path: str, output_path: str = None,
               max_chars: int = DEFAULT_MAX_CHARS,
               overlap: int = DEFAULT_OVERLAP) -> list[dict]:
    """
    Read a text file, chunk it, and optionally save to JSON.

    Args:
        input_path: Path to input text file
        output_path: Path for JSON output (optional)
        max_chars: Max chars per chunk
        overlap: Overlap between chunks

    Returns:
        List of chunk dicts
    """
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = chunk_text(text, max_chars=max_chars, overlap=overlap)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        logger.info(f"Chunks saved to {output_path}")

    return chunks


def main():
    parser = argparse.ArgumentParser(
        description="Split plaintext into chunks for AI processing"
    )
    parser.add_argument("--input", "-i", required=False,
                        help="Input text file path")
    parser.add_argument("--text", "-t", required=False,
                        help="Input text (direct)")
    parser.add_argument("--output", "-o", default=None,
                        help="Output JSON file path")
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS,
                        help=f"Max chars per chunk (default: {DEFAULT_MAX_CHARS})")
    parser.add_argument("--overlap", type=int, default=DEFAULT_OVERLAP,
                        help=f"Overlap between chunks (default: {DEFAULT_OVERLAP})")

    args = parser.parse_args()

    if args.input:
        chunks = chunk_file(args.input, args.output, args.max_chars, args.overlap)
    elif args.text:
        chunks = chunk_text(args.text, args.max_chars, args.overlap)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)
    else:
        parser.error("Either --input or --text is required")

    print(f"Created {len(chunks)} chunks:")
    for c in chunks:
        print(f"  Chunk {c['index']}: {c['char_count']} chars "
              f"(chars {c['start_char']}-{c['end_char']})")


if __name__ == "__main__":
    main()
