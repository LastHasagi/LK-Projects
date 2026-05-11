import pytest

from app.core.rag.chunker import chunk_text, estimate_tokens


def test_estimate_tokens_rough():
    assert estimate_tokens("a" * 400) == pytest.approx(100, rel=0.2)


def test_chunk_text_respects_max_and_overlap():
    text = " ".join([f"palavra{i}" for i in range(1000)])
    chunks = chunk_text(text, max_tokens=100, overlap_tokens=10)
    assert len(chunks) >= 2
    assert all(estimate_tokens(c) <= 120 for c in chunks)
    suffix = chunks[0][-30:]
    assert any(token in chunks[1] for token in suffix.split())


def test_chunk_text_empty_input():
    assert chunk_text("", max_tokens=100, overlap_tokens=10) == []
