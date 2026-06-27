"""
Tests für die KI-Extraktion Pipeline (AP4).
Testet chunk_text, merge_positions, save_position (mocked DB).
"""
import json
from unittest.mock import MagicMock, patch
from packages.extraction.src.extract import (
    chunk_text,
    merge_positions,
    load_prompt,
    call_extraction_model,
    VALID_POSITION_TYPES,
)


class TestChunkText:
    """Test text chunking with overlap"""

    def test_short_text_returns_single_chunk(self):
        text = "Kurzer Text."
        chunks = chunk_text(text, max_chars=4000, overlap=200)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_split_into_chunks(self):
        text = "A" * 10000
        chunks = chunk_text(text, max_chars=4000, overlap=200)
        assert len(chunks) > 1
        assert all(len(c) <= 4000 for c in chunks)

    def test_overlap_between_chunks(self):
        text = "ABCDEFGHIJ" * 1000  # 10000 chars
        chunks = chunk_text(text, max_chars=4000, overlap=200)
        # Second chunk should start 200 chars before end of first chunk
        assert chunks[1][:200] == chunks[0][-200:]

    def test_empty_text(self):
        chunks = chunk_text("", max_chars=4000, overlap=200)
        assert chunks == [""]


class TestMergePositions:
    """Test merging positions from multiple chunks"""

    def test_non_unklar_overrides_unklar(self):
        results = [
            {"positions": [
                {"thesis_id": "t1", "position_type": "unklar", "quote": None, "quote_location": None},
                {"thesis_id": "t2", "position_type": "zustimmen", "quote": "Zitat A", "quote_location": {"page": 1}},
            ]},
            {"positions": [
                {"thesis_id": "t1", "position_type": "ablehnen", "quote": "Zitat B", "quote_location": {"page": 2}},
                {"thesis_id": "t2", "position_type": "unklar", "quote": None, "quote_location": None},
            ]},
        ]
        merged = merge_positions(results)
        assert merged["t1"]["position_type"] == "ablehnen"
        assert merged["t2"]["position_type"] == "zustimmen"

    def test_last_non_unklar_wins(self):
        results = [
            {"positions": [
                {"thesis_id": "t1", "position_type": "zustimmen", "quote": "Erstes Zitat hier.", "quote_location": {"page": 1}},
            ]},
            {"positions": [
                {"thesis_id": "t1", "position_type": "ablehnen", "quote": "Zweites Zitat hier.", "quote_location": {"page": 2}},
            ]},
        ]
        merged = merge_positions(results)
        assert merged["t1"]["position_type"] == "ablehnen"

    def test_all_unklar_stays_unklar(self):
        results = [
            {"positions": [
                {"thesis_id": "t1", "position_type": "unklar", "quote": None, "quote_location": None},
            ]},
            {"positions": [
                {"thesis_id": "t1", "position_type": "unklar", "quote": None, "quote_location": None},
            ]},
        ]
        merged = merge_positions(results)
        assert merged["t1"]["position_type"] == "unklar"

    def test_empty_results(self):
        merged = merge_positions([])
        assert merged == {}


class TestLoadPrompt:
    """Test loading the extraction prompt"""

    def test_prompt_loads(self):
        prompt = load_prompt()
        assert "Extraktions-Prompt" in prompt
        assert "zustimmen" in prompt
        assert "JSON" in prompt


class TestCallExtractionModel:
    """Test the model call (mock)"""

    def test_mock_returns_unklar_for_all_theses(self):
        theses = [
            {"id": "t1", "statement": "Test These 1"},
            {"id": "t2", "statement": "Test These 2"},
        ]
        result = call_extraction_model("prompt", theses, "chunk text", "gpt-4o")
        assert "positions" in result
        assert len(result["positions"]) == 2
        for pos in result["positions"]:
            assert pos["position_type"] == "unklar"
