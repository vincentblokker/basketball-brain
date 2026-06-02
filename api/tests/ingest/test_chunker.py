from app.ingest.chunker import recursive_chunk


def test_chunks_respect_size_and_overlap():
    text = "a" * 10000
    chunks = recursive_chunk(text, chunk_size=800, overlap=160)
    assert all(len(c) <= 1000 for c in chunks)
    assert len(chunks) >= 10


def test_chunks_split_on_paragraph_boundaries():
    text = "Para1.\n\n" + ("Para2 sentence. " * 100) + "\n\nPara3."
    chunks = recursive_chunk(text, chunk_size=400, overlap=80)
    # Para3 should not appear in the first chunk
    assert "Para3" not in chunks[0]


def test_empty_text_returns_empty_list():
    assert recursive_chunk("") == []


def test_short_text_returns_single_chunk():
    text = "Korte tekst onder de chunk-size."
    chunks = recursive_chunk(text, chunk_size=800, overlap=160)
    assert len(chunks) == 1
    assert chunks[0] == text
