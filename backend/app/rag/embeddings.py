from typing import List
import structlog
from app.providers.embeddings.registry import get_embedding_provider, EMBEDDING_PROVIDER_OPTIONS

logger = structlog.get_logger()

class EmbeddingService:
    @classmethod
    async def embed_with_provider(
        cls,
        texts: List[str],
        provider_name: str,
        model: str,
        api_key: str = "",
        ollama_url: str = "",
    ) -> List[List[float]]:
        kwargs = {}
        if provider_name == "ollama" and ollama_url:
            kwargs["base_url"] = ollama_url
            
        provider = get_embedding_provider(provider_name, api_key=api_key, **kwargs)
        if not provider:
            raise ValueError(f"Unknown embedding provider: {provider_name}")
            
        response = await provider.embeddings(texts, model=model)
        return response.embeddings

    @classmethod
    def get_dimension(cls, model_name: str) -> int:
        for provider_info in EMBEDDING_PROVIDER_OPTIONS.values():
            for m in provider_info["models"]:
                if m["id"] == model_name:
                    return m["dim"]
        return 384
