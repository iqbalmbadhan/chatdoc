from typing import List, Optional
import structlog

logger = structlog.get_logger()


class EmbeddingService:
    """Generates embeddings using local sentence-transformers or a provider."""

    _model = None
    _model_name: str = ""

    @classmethod
    def get_local_model(cls, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        if cls._model is None or cls._model_name != model_name:
            from sentence_transformers import SentenceTransformer
            cls._model = SentenceTransformer(model_name)
            cls._model_name = model_name
            logger.info("Embedding model loaded", model=model_name)
        return cls._model

    @classmethod
    async def embed_texts_local(cls, texts: List[str], model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> List[List[float]]:
        model = cls.get_local_model(model_name)
        embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()

    @classmethod
    async def embed_texts(cls, texts: List[str], provider=None, model: str = "") -> List[List[float]]:
        if provider:
            response = await provider.embeddings(texts, model=model)
            return response.embeddings
        return await cls.embed_texts_local(texts)

    @classmethod
    def get_dimension(cls, model_name: str) -> int:
        dimensions = {
            "sentence-transformers/all-MiniLM-L6-v2": 384,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-004": 768,
            "nomic-embed-text": 768,
        }
        return dimensions.get(model_name, 384)
