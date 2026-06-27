"""
Tests for parse_html.py — HTML text extraction from mock content.
"""
import sys
import os
import json
import tempfile
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from parse_html import extract_paragraphs, parse_html_content, build_css_path, Paragraph
from bs4 import BeautifulSoup


MOCK_HTML_PROGRAM = """
<html>
<head>
    <title>Wahlprogramm 2025</title>
    <style>body { color: black; }</style>
    <script>console.log("hello");</script>
</head>
<body>
    <header><nav><a href="/">Home</a></nav></header>
    <main>
        <h1>Unser Wahlprogramm</h1>
        <p>Wir setzen uns ein für eine gerechte Gesellschaft.</p>
        <p>Klimaschutz ist die wichtigste Aufgabe unserer Zeit.</p>
        <div class="chapter">
            <h2>Wirtschaft</h2>
            <p>Wir stärken den Mittelstand und fördern Innovation.</p>
            <ul>
                <li>Steuerentlastung für kleine Unternehmen</li>
                <li>Investitionen in Bildung und Forschung</li>
            </ul>
        </div>
        <div class="chapter">
            <h2>Soziales</h2>
            <p>Wir garantieren eine starke Rente und gute Pflege.</p>
            <blockquote>Sozialer Zusammenhalt ist das Fundament unserer Demokratie.</blockquote>
        </div>
    </main>
    <footer><p>Impressum</p></footer>
</body>
</html>
"""


class TestExtractParagraphs:
    def test_extract_basic_paragraphs(self):
        paragraphs = extract_paragraphs(MOCK_HTML_PROGRAM)
        assert len(paragraphs) > 0
        texts = [p.text for p in paragraphs]
        assert "Wir setzen uns ein für eine gerechte Gesellschaft." in texts

    def test_extracts_headings(self):
        paragraphs = extract_paragraphs(MOCK_HTML_PROGRAM)
        texts = [p.text for p in paragraphs]
        assert "Unser Wahlprogramm" in texts
        assert "Wirtschaft" in texts

    def test_extracts_list_items(self):
        paragraphs = extract_paragraphs(MOCK_HTML_PROGRAM)
        texts = [p.text for p in paragraphs]
        assert "Steuerentlastung für kleine Unternehmen" in texts

    def test_extracts_blockquote(self):
        paragraphs = extract_paragraphs(MOCK_HTML_PROGRAM)
        texts = [p.text for p in paragraphs]
        assert "Sozialer Zusammenhalt ist das Fundament unserer Demokratie." in texts

    def test_skips_script_style(self):
        paragraphs = extract_paragraphs(MOCK_HTML_PROGRAM)
        texts = [p.text for p in paragraphs]
        # Script and style content should not appear
        assert not any("color: black" in t for t in texts)
        assert not any("console.log" in t for t in texts)

    def test_skips_nav_footer(self):
        paragraphs = extract_paragraphs(MOCK_HTML_PROGRAM)
        texts = [p.text for p in paragraphs]
        # Nav and footer content should be removed
        assert "Home" not in texts
        assert "Impressum" not in texts

    def test_paragraph_has_css_path(self):
        paragraphs = extract_paragraphs(MOCK_HTML_PROGRAM)
        for p in paragraphs:
            assert p.css_path  # non-empty
            assert p.tag  # has tag name

    def test_paragraph_has_index(self):
        paragraphs = extract_paragraphs(MOCK_HTML_PROGRAM)
        indices = [p.index for p in paragraphs]
        assert indices == list(range(len(paragraphs)))

    def test_deduplication(self):
        """Nested divs with same text should not produce duplicates."""
        html = """
        <html><body>
        <div><p>Duplicate text here</p></div>
        <div><p>Duplicate text here</p></div>
        </body></html>
        """
        paragraphs = extract_paragraphs(html)
        texts = [p.text for p in paragraphs]
        # "Duplicate text here" appears in both p tags, should have 2 entries
        # (they're separate <p> elements, not nested)
        assert texts.count("Duplicate text here") == 2

    def test_nested_deduplication(self):
        """Nested divs that share text should deduplicate."""
        html = """
        <html><body>
        <div>
            <div>
                <p>This is a paragraph with enough text to be included</p>
            </div>
        </div>
        </body></html>
        """
        paragraphs = extract_paragraphs(html)
        # Should not have duplicates from nested divs
        texts = [p.text for p in paragraphs]
        assert len(texts) == len(set(texts))


class TestParseHtmlContent:
    def test_parse_returns_text(self):
        result = parse_html_content(MOCK_HTML_PROGRAM)
        assert "text" in result
        assert "Wirtschaft" in result["text"]
        assert "paragraphs" in result

    def test_parse_writes_output_file(self, tmp_path):
        output_file = tmp_path / "output.txt"
        result = parse_html_content(MOCK_HTML_PROGRAM, str(output_file))
        assert output_file.exists()
        assert result["text_path"] == str(output_file)
        content = output_file.read_text(encoding="utf-8")
        assert "Wirtschaft" in content

    def test_parse_writes_json_file(self, tmp_path):
        json_file = tmp_path / "output.json"
        result = parse_html_content(MOCK_HTML_PROGRAM, output_json=str(json_file))
        assert json_file.exists()
        data = json.loads(json_file.read_text(encoding="utf-8"))
        assert "paragraphs" in data
        assert len(data["paragraphs"]) > 0
        assert "css_path" in data["paragraphs"][0]

    def test_paragraph_count(self):
        result = parse_html_content(MOCK_HTML_PROGRAM)
        assert result["paragraph_count"] > 0


class TestBuildCssPath:
    def test_css_path_for_simple_element(self):
        html = '<html><body><div id="main"><p>Test text here</p></div></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        p = soup.find("p")
        path = build_css_path(p)
        assert "p" in path
        assert "#main" in path

    def test_css_path_with_classes(self):
        html = '<html><body><div class="content article"><p>Test text here</p></div></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        p = soup.find("p")
        path = build_css_path(p)
        assert "content" in path or "article" in path


class TestEmptyInput:
    def test_empty_html(self):
        paragraphs = extract_paragraphs("")
        assert len(paragraphs) == 0

    def test_html_with_no_content(self):
        html = "<html><head></head><body></body></html>"
        paragraphs = extract_paragraphs(html)
        assert len(paragraphs) == 0

    def test_html_with_only_script(self):
        html = "<html><body><script>alert(1)</script></body></html>"
        paragraphs = extract_paragraphs(html)
        assert len(paragraphs) == 0
