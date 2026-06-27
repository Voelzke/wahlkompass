"""
Tests for parse_pdf.py — PDF text extraction with generated test PDFs.

Uses reportlab to generate small test PDFs on the fly.
"""
import sys
import os
import tempfile
import pytest
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from parse_pdf import parse_pdf_file, extract_text_from_pdf, detect_page_number


def generate_test_pdf(output_path: str, pages: list[str] = None, add_page_numbers: bool = False):
    """
    Generate a small test PDF using reportlab.

    Args:
        output_path: Where to save the PDF
        pages: List of text content per page
        add_page_numbers: If True, add page numbers at bottom
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    if pages is None:
        pages = [
            "Dies ist die erste Seite des Test-PDFs. "
            "Sie enthält einigen Beispieltext für die Extraktion. "
            "Wir testen hier die Funktionalität des PDF-Parsers.",
            "Dies ist die zweite Seite. "
            "Hier steht weiterer Text zum Testen. "
            "Die Extraktion sollte alle Seiten korrekt erfassen.",
        ]

    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    for i, content in enumerate(pages):
        # Write text
        c.drawString(100, height - 100, content[:80])
        if len(content) > 80:
            c.drawString(100, height - 120, content[80:160])
        if len(content) > 160:
            c.drawString(100, height - 140, content[160:])

        # Add page number at bottom
        if add_page_numbers:
            c.drawCentredString(width / 2, 40, str(i + 1))

        c.showPage()

    c.save()
    return output_path


@pytest.fixture
def test_pdf(tmp_path):
    """Create a test PDF with 3 pages."""
    pdf_path = tmp_path / "test_program.pdf"
    generate_test_pdf(str(pdf_path), pages=[
        "Seite eins: Wirtschaftspolitik ist wichtig für das Land. "
        "Wir müssen Investitionen fördern und Steuern senken.",
        "Seite zwei: Klimaschutz ist eine zentrale Herausforderung. "
        "Wir setzen uns für erneuerbare Energien ein.",
        "Seite drei: Bildung ist die Zukunft. "
        "Wir investieren in Schulen und Universitäten.",
    ])
    return pdf_path


@pytest.fixture
def test_pdf_with_page_numbers(tmp_path):
    """Create a test PDF with page numbers."""
    pdf_path = tmp_path / "test_pagenumbers.pdf"
    generate_test_pdf(str(pdf_path), add_page_numbers=True)
    return pdf_path


class TestDetectPageNumber:
    def test_detect_simple_number(self):
        assert detect_page_number("Some text\n\nMore text\n\n42")

    def test_detect_seite_pattern(self):
        assert detect_page_number("Text content\n\nSeite 5")

    def test_detect_s_pattern(self):
        assert detect_page_number("Text content\n\nS. 10")

    def test_detect_slash_pattern(self):
        assert detect_page_number("Text content\n\n3/42")

    def test_no_page_number(self):
        assert not detect_page_number("Just some regular text without any numbers at the end here")

    def test_empty_text(self):
        assert not detect_page_number("")

    def test_none_text(self):
        assert not detect_page_number(None)


class TestExtractTextFromPdf:
    def test_extract_3_pages(self, test_pdf):
        pages, count, has_pn = extract_text_from_pdf(str(test_pdf))
        assert count == 3
        assert len(pages) == 3

    def test_extracted_text_contains_content(self, test_pdf):
        pages, count, has_pn = extract_text_from_pdf(str(test_pdf))
        all_text = " ".join(pages)
        assert "Wirtschaftspolitik" in all_text or "Seite eins" in all_text
        assert "Klimaschutz" in all_text or "Seite zwei" in all_text

    def test_no_page_numbers_detected(self, test_pdf):
        pages, count, has_pn = extract_text_from_pdf(str(test_pdf))
        assert has_pn == False

    def test_page_numbers_detected(self, test_pdf_with_page_numbers):
        pages, count, has_pn = extract_text_from_pdf(str(test_pdf_with_page_numbers))
        assert count == 2
        assert has_pn == True


class TestParsePdfFile:
    def test_parse_returns_result(self, test_pdf):
        result = parse_pdf_file(str(test_pdf))
        assert "text_path" in result
        assert "page_count" in result
        assert "has_page_numbers" in result
        assert "pages" in result

    def test_parse_page_count_correct(self, test_pdf):
        result = parse_pdf_file(str(test_pdf))
        assert result["page_count"] == 3

    def test_parse_creates_output_file(self, test_pdf, tmp_path):
        output_path = tmp_path / "output.txt"
        result = parse_pdf_file(str(test_pdf), str(output_path))
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "--- PAGE 1 ---" in content
        assert "--- PAGE 2 ---" in content
        assert "--- PAGE 3 ---" in content

    def test_parse_default_output_path(self, test_pdf):
        result = parse_pdf_file(str(test_pdf))
        # Default output is same name with .txt extension
        expected_path = str(test_pdf.with_suffix(".txt"))
        assert result["text_path"] == expected_path
        assert Path(expected_path).exists()

    def test_parse_pages_list(self, test_pdf):
        result = parse_pdf_file(str(test_pdf))
        assert len(result["pages"]) == 3
        # Each page should be a string
        for page_text in result["pages"]:
            assert isinstance(page_text, str)

    def test_parse_nonexistent_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            parse_pdf_file(str(tmp_path / "nonexistent.pdf"))

    def test_parse_has_page_numbers_flag(self, test_pdf):
        result = parse_pdf_file(str(test_pdf))
        assert result["has_page_numbers"] == False

    def test_parse_with_page_numbers(self, test_pdf_with_page_numbers):
        result = parse_pdf_file(str(test_pdf_with_page_numbers))
        assert result["has_page_numbers"] == True


class TestSinglePagePdf:
    def test_single_page(self, tmp_path):
        pdf_path = tmp_path / "single.pdf"
        generate_test_pdf(str(pdf_path), pages=["Only one page of text content here."])
        result = parse_pdf_file(str(pdf_path))
        assert result["page_count"] == 1
        assert len(result["pages"]) == 1
