import numpy as np

from app.retrieval.embeddings import Embedder


def test_embeddings_have_correct_shape():
    e = Embedder()
    vectors = e.embed(["test sentence", "another sentence"])
    assert vectors.shape == (2, 1024)
    assert vectors.dtype == np.float32


def test_similar_sentences_are_close():
    e = Embedder()
    vectors = e.embed([
        "Wat zijn de regels van basketbal?",
        "Welke regels gelden in basketbal?",
        "Wat is de prijs van een banaan?",
    ])
    from numpy.linalg import norm

    def cos(a: np.ndarray, b: np.ndarray) -> float:
        return float(a @ b / (norm(a) * norm(b)))

    sim_ab = cos(vectors[0], vectors[1])
    sim_ac = cos(vectors[0], vectors[2])
    assert sim_ab > sim_ac, (
        f"Expected basketbal-pair ({sim_ab:.3f}) closer than "
        f"basketbal-vs-banaan ({sim_ac:.3f})"
    )


def test_embed_query_returns_1d_vector():
    e = Embedder()
    vec = e.embed_query("Hoe lang is de shot clock?")
    assert vec.shape == (1024,)
    assert vec.dtype == np.float32
