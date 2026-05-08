import numpy as np
from sentence_transformers import SentenceTransformer


class Embedder:
    """Singleton wrapper around bge-m3. Lazy-loads model on first use.

    bge-m3 is multilingual (100+ languages, strong on Dutch and English),
    1024-dim, MIT-licensed, locally runnable. See [[Embedding Models 2026]] in vault.
    """

    _model: SentenceTransformer | None = None

    def __init__(self, model_name: str = "BAAI/bge-m3"):
        self.model_name = model_name

    def _ensure_loaded(self) -> SentenceTransformer:
        if Embedder._model is None:
            Embedder._model = SentenceTransformer(self.model_name)
        return Embedder._model

    def embed(self, texts: list[str]) -> np.ndarray:
        model = self._ensure_loaded()
        result = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        return np.asarray(result, dtype=np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return np.asarray(self.embed([text])[0], dtype=np.float32)
