"""
Setup file for the wahlkompass-scraping package.
"""
from setuptools import setup

setup(
    name="wahlkompass-scraping",
    version="0.1.0",
    description="Scraping pipeline for Wahlkompass",
    package_dir={"": "src"},
    py_modules=["discover_parties", "download_programs", "parse_pdf",
                "parse_html", "chunk_text"],
    install_requires=[
        "httpx>=0.27,<1",
        "pdfplumber>=0.11,<1",
        "beautifulsoup4>=4.12,<5",
        "pytesseract>=0.3.10,<1",
    ],
    entry_points={
        "console_scripts": [
            "wahlkompass-discover-parties=discover_parties:main",
            "wahlkompass-download-programs=download_programs:main",
            "wahlkompass-parse-pdf=parse_pdf:main",
            "wahlkompass-parse-html=parse_html:main",
            "wahlkompass-chunk-text=chunk_text:main",
        ],
    },
    python_requires=">=3.12",
)
