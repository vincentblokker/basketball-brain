import re

from rank_bm25 import BM25Okapi

from app.schemas import Chunk

_TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


class BM25Index:
    """In-memory BM25 lexical index over chunks. Rebuilt at startup
    by reading all chunks from the vector store.
    """

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        if not chunks:
            self.bm25: BM25Okapi | None = None
            self.id_by_idx: dict[int, str] = {}
            return
        corpus = [_tokenize(self._embed_text(c)) for c in chunks]
        self.bm25 = BM25Okapi(corpus)
        self.id_by_idx = {i: c.chunk_id for i, c in enumerate(chunks)}

    def query(self, question: str, top_k: int = 50) -> list[str]:
        if self.bm25 is None:
            return []
        scores = self.bm25.get_scores(_tokenize(question))
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [self.id_by_idx[i] for i in ranked]

    @staticmethod
    def _embed_text(c: Chunk) -> str:
        if c.contextual_prefix:
            return f"{c.contextual_prefix}\n\n{c.text}"
        return c.text
