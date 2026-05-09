from typing import Dict, Optional, Type
from app.providers.embeddings.base import BaseEmbeddingProvider
from app.providers.embeddings.openai_provider import OpenAIEmbeddingProvider
from app.providers.embeddings.gemini_provider import GeminiEmbeddingProvider
from app.providers.embeddings.ollama_provider import OllamaEmbeddingProvider
from app.providers.embeddings.local_provider import LocalEmbeddingProvider

EMBEDDING_PROVIDER_REGISTRY: Dict[str, Type[BaseEmbeddingProvider]] = {
    "local": LocalEmbeddingProvider,
    "openai": OpenAIEmbeddingProvider,
    "gemini": GeminiEmbeddingProvider,
    "ollama": OllamaEmbeddingProvider,
}

# Available embedding providers with their supported models and vector dimensions
EMBEDDING_PROVIDER_OPTIONS: Dict[str, dict] = {
    "local": {
        "display_name": "Local (sentence-transformers)",
        "requires_api_key": False,
        "models": [
            {"id": "BAAI/bge-small-en-v1.5", "dim": 384},
            {"id": "nomic-embed-text", "dim": 768},
            {"id": "sentence-transformers/all-MiniLM-L6-v2", "dim": 384},
        ],
    },
    "openai": {
        "display_name": "OpenAI",
        "requires_api_key": True,
        "models": [
            {"id": "text-embedding-3-small", "dim": 1536},
            {"id": "text-embedding-3-large", "dim": 3072},
            {"id": "text-embedding-ada-002", "dim": 1536},
        ],
    },
    "gemini": {
        "display_name": "Google Gemini",
        "requires_api_key": True,
        "models": [
            {"id": "text-embedding-004", "dim": 768},
        ],
    },
    "ollama": {
        "display_name": "Ollama (Local)",
        "requires_api_key": False,
        "models": [
            {"id": "nomic-embed-text", "dim": 768},
            {"id": "mxbai-embed-large", "dim": 1024},
            {"id": "all-minilm", "dim": 384},
        ],
    },
}

def get_embedding_provider(name: str, api_key: str = "", **kwargs) -> Optional[BaseEmbeddingProvider]:
    cls = EMBEDDING_PROVIDER_REGISTRY.get(name)
    if not cls:
        return None
    return cls(api_key=api_key, **kwargs)
