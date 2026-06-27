"""Root conftest.py — add all package src directories to sys.path."""
import os
import sys
from pathlib import Path

root = Path(__file__).parent
for src_dir in [
    root / "packages" / "scraping" / "src",
    root / "packages" / "extraction" / "src",
    root / "packages" / "db",
    root / "review",
]:
    src_str = str(src_dir)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)
