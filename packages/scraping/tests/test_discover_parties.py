"""
Tests for discover_parties.py — party list parsing from mock HTML.
"""
import sys
import os
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from discover_parties import parse_party_list_html, PartyListParser


MOCK_BUNDESWAHLLEITER_HTML = """
<html>
<body>
<h1>Listen zugelassener Parteien</h1>
<table>
<tr><th>Name der Partei</th><th>Kurzbezeichnung</th><th>Website</th></tr>
<tr><td>Sozialdemokratische Partei Deutschlands</td><td>SPD</td><td>https://www.spd.de</td></tr>
<tr><td>Christlich Demokratische Union Deutschlands</td><td>CDU</td><td>https://www.cdu.de</td></tr>
<tr><td>Bündnis 90/Die Grünen</td><td>GRÜNE</td><td>https://www.gruene.de</td></tr>
<tr><td>Freie Demokratische Partei</td><td>FDP</td><td>https://www.fdp.de</td></tr>
<tr><td>Alternative für Deutschland</td><td>AfD</td><td>https://www.afd.de</td></tr>
<tr><td>Die Linke</td><td>LINKE</td><td>https://www.dielinke.de</td></tr>
</table>
</body>
</html>
"""

MOCK_MINIMAL_HTML = """
<html><body>
<table>
<tr><td>Partei A</td><td>PA</td></tr>
<tr><td>Partei B</td><td>PB</td></tr>
</table>
</body></html>
"""

MOCK_EMPTY_HTML = """
<html><body><p>No parties here.</p></body></html>
"""


class TestParsePartyListHtml:
    def test_parse_bundeswahlleiter_format(self):
        parties = parse_party_list_html(MOCK_BUNDESWAHLLEITER_HTML)
        assert len(parties) == 6
        assert parties[0]["name"] == "Sozialdemokratische Partei Deutschlands"
        assert parties[0]["short_name"] == "SPD"
        assert parties[0]["website_url"] == "https://www.spd.de"

    def test_parse_all_parties_have_names(self):
        parties = parse_party_list_html(MOCK_BUNDESWAHLLEITER_HTML)
        for p in parties:
            assert p["name"]
            assert p["short_name"]

    def test_parse_minimal_table(self):
        parties = parse_party_list_html(MOCK_MINIMAL_HTML)
        assert len(parties) == 2
        assert parties[0]["name"] == "Partei A"
        assert parties[1]["name"] == "Partei B"

    def test_parse_empty_html(self):
        parties = parse_party_list_html(MOCK_EMPTY_HTML)
        assert len(parties) == 0

    def test_header_row_skipped(self):
        parties = parse_party_list_html(MOCK_BUNDESWAHLLEITER_HTML)
        # First entry should be SPD, not "Name der Partei"
        assert parties[0]["name"] != "Name der Partei"

    def test_website_url_extracted(self):
        parties = parse_party_list_html(MOCK_BUNDESWAHLLEITER_HTML)
        for p in parties:
            # All data rows in the mock have website URLs
            if p["name"] != "Name der Partei":
                assert p["website_url"] is not None
                assert p["website_url"].startswith("http")

    def test_short_name_max_20_chars(self):
        parties = parse_party_list_html(MOCK_BUNDESWAHLLEITER_HTML)
        for p in parties:
            assert len(p["short_name"]) <= 20

    def test_auto_generate_short_name(self):
        """Short name should be generated if missing."""
        html = """
        <table>
        <tr><th>Name</th><th>Kurz</th></tr>
        <tr><td>Some Very Long Party Name Without Short</td><td></td></tr>
        </table>
        """
        parties = parse_party_list_html(html)
        assert len(parties) == 1
        assert parties[0]["name"] == "Some Very Long Party Name Without Short"
        # Should generate initials
        assert parties[0]["short_name"]  # non-empty
        assert len(parties[0]["short_name"]) <= 20

    def test_non_http_website_ignored(self):
        html = """
        <table>
        <tr><th>Name</th><th>Kurz</th><th>Website</th></tr>
        <tr><td>Test Party</td><td>TP</td><td>not-a-url</td></tr>
        </table>
        """
        parties = parse_party_list_html(html)
        assert len(parties) == 1
        assert parties[0]["website_url"] is None


class TestPartyListParserClass:
    def test_parser_instance(self):
        parser = PartyListParser()
        parser.feed(MOCK_BUNDESWAHLLEITER_HTML)
        assert len(parser.parties) == 6

    def test_parser_idempotent(self):
        """Running parser twice on same content gives consistent results."""
        parties1 = parse_party_list_html(MOCK_BUNDESWAHLLEITER_HTML)
        parties2 = parse_party_list_html(MOCK_BUNDESWAHLLEITER_HTML)
        assert len(parties1) == len(parties2)
        for p1, p2 in zip(parties1, parties2):
            assert p1["name"] == p2["name"]
