"""
Tests for chunk_text.py — text chunking correctness.
"""
import sys
import os
import json
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from chunk_text import chunk_text, chunk_file, split_long_text


class TestChunkText:
    def test_empty_text(self):
        chunks = chunk_text("")
        assert len(chunks) == 0

    def test_short_text_one_chunk(self):
        text = "This is a short text that fits in one chunk."
        chunks = chunk_text(text, max_chars=4000, overlap=200)
        assert len(chunks) == 1
        assert chunks[0]["text"] == text
        assert chunks[0]["char_count"] == len(text)

    def test_long_text_multiple_chunks(self):
        """Text exceeding max_chars should produce multiple chunks."""
        paragraphs = [f"Paragraph {i}: " + "x" * 200 for i in range(50)]
        text = "\n\n".join(paragraphs)
        chunks = chunk_text(text, max_chars=500, overlap=50)
        assert len(chunks) > 1

    def test_max_chars_respected(self):
        """No chunk should exceed max_chars (plus overlap)."""
        paragraphs = [f"Paragraph {i} with some content " + "y" * 100 for i in range(30)]
        text = "\n\n".join(paragraphs)
        chunks = chunk_text(text, max_chars=400, overlap=50)
        for chunk in chunks:
            # Allow some slack for overlap
            assert chunk["char_count"] <= 400 + 50 + 20  # max_chars + overlap + separator

    def test_overlap_present(self):
        """Consecutive chunks should share overlap text."""
        text = "\n\n".join([f"Para {i}: " + "z" * 300 for i in range(20)])
        chunks = chunk_text(text, max_chars=500, overlap=100)
        if len(chunks) >= 2:
            # The end of chunk 0 should appear at the start of chunk 1
            end_of_0 = chunks[0]["text"][-50:]
            assert end_of_0 in chunks[1]["text"]

    def test_chunk_indices_sequential(self):
        text = "\n\n".join([f"Para {i}: " + "a" * 200 for i in range(30)])
        chunks = chunk_text(text, max_chars=500, overlap=50)
        indices = [c["index"] for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_chunk_has_required_fields(self):
        chunks = chunk_text("Some text here that is long enough.", max_chars=4000, overlap=200)
        for chunk in chunks:
            assert "text" in chunk
            assert "index" in chunk
            assert "char_count" in chunk
            assert "start_char" in chunk
            assert "end_char" in chunk

    def test_start_end_char_correct(self):
        text = "Hello world this is a test."
        chunks = chunk_text(text, max_chars=4000, overlap=200)
        assert chunks[0]["start_char"] == 0
        assert chunks[0]["end_char"] == len(text)

    def test_paragraph_boundaries_respected(self):
        """Chunks should not split mid-paragraph when possible."""
        para1 = "A" * 100
        para2 = "B" * 100
        para3 = "C" * 100
        text = f"{para1}\n\n{para2}\n\n{para3}"
        chunks = chunk_text(text, max_chars=150, overlap=0)
        # Each chunk should contain complete paragraphs
        for chunk in chunks:
            # Should not contain partial "A"s and "B"s mixed
            if "A" in chunk["text"] and "B" in chunk["text"]:
                # This is fine if both paragraphs fit
                pass
            # But should never split a single paragraph
            assert not ("A" in chunk["text"] and chunk["text"].count("A") < 100 and "B" in chunk["text"] and chunk["text"].count("B") < 100)

    def test_zero_overlap(self):
        text = "\n\n".join([f"Para {i}: " + "x" * 200 for i in range(20)])
        chunks = chunk_text(text, max_chars=500, overlap=0)
        assert len(chunks) > 1

    def test_custom_max_chars(self):
        text = "A" * 100 + "\n\n" + "B" * 100 + "\n\n" + "C" * 100
        chunks = chunk_text(text, max_chars=120, overlap=0)
        assert len(chunks) >= 2

    def test_all_text_covered(self):
        """The union of all chunks should cover the entire text."""
        text = "\n\n".join([f"Paragraph {i}: " + "content " * 20 for i in range(20)])
        chunks = chunk_text(text, max_chars=300, overlap=50)
        # First chunk starts at 0
        assert chunks[0]["start_char"] == 0
        # Last chunk should reach near the end
        assert chunks[-1]["end_char"] >= len(text) - 300  # last chunk covers most text


class TestSplitLongText:
    def test_split_long_text(self):
        text = "A" * 1000
        chunks = split_long_text(text, max_chars=300, overlap=50)
        assert len(chunks) > 1
        for c in chunks:
            assert len(c["text"]) <= 300

    def test_split_at_word_boundary(self):
        text = "word " * 200  # 1000 chars
        chunks = split_long_text(text, max_chars=300, overlap=50)
        # Should prefer splitting at spaces
        for c in chunks:
            assert len(c["text"]) <= 300

    def test_split_start_end_correct(self):
        text = "A" * 1000
        chunks = split_long_text(text, max_chars=300, overlap=50)
        assert chunks[0]["start"] == 0
        assert chunks[-1]["end"] == 1000


class TestChunkFile:
    def test_chunk_file(self, tmp_path):
        text = "\n\n".join([f"Para {i}: " + "x" * 200 for i in range(20)])
        input_path = tmp_path / "input.txt"
        input_path.write_text(text, encoding="utf-8")

        chunks = chunk_file(str(input_path))
        assert len(chunks) > 0
        assert chunks[0]["text"]  # non-empty

    def test_chunk_file_with_output(self, tmp_path):
        text = "\n\n".join([f"Para {i}: " + "x" * 200 for i in range(20)])
        input_path = tmp_path / "input.txt"
        output_path = tmp_path / "chunks.json"
        input_path.write_text(text, encoding="utf-8")

        chunks = chunk_file(str(input_path), str(output_path))
        assert output_path.exists()
        loaded = json.loads(output_path.read_text(encoding="utf-8"))
        assert len(loaded) == len(chunks)
        assert loaded[0]["text"] == chunks[0]["text"]

    def test_chunk_file_empty(self, tmp_path):
        input_path = tmp_path / "empty.txt"
        input_path.write_text("", encoding="utf-8")
        chunks = chunk_file(str(input_path))
        assert len(chunks) == 0


class TestEdgeCases:
    def test_single_word(self):
        chunks = chunk_text("Hello")
        assert len(chunks) == 1
        assert chunks[0]["text"] == "Hello"

    def test_only_whitespace(self):
        chunks = chunk_text("   \n\n  \n  ")
        assert len(chunks) == 0

    def test_negative_overlap_raises(self):
        with pytest.raises(ValueError):
            chunk_text("test", overlap=-1)

    def test_overlap_ge_max_chars_raises(self):
        with pytest.raises(ValueError):
            chunk_text("test", max_chars=100, overlap=100)

    def test_zero_max_chars_raises(self):
        with pytest.raises(ValueError):
            chunk_text("test", max_chars=0)

    def test_very_large_overlap(self):
        """Overlap close to max_chars should still work."""
        text = "A" * 50 + "\n\n" + "B" * 50
        chunks = chunk_text(text, max_chars=100, overlap=90)
        assert len(chunks) >= 1
