from typing import List
from sentence_transformers import SentenceTransformer
from app.providers.embeddings.base import BaseEmbeddingProvider, EmbeddingResponse
import asyncio

class LocalEmbeddingProvider(BaseEmbeddingProvider):
    name = "local"
    display_name = "Local (Sentence-Transformers)"

    _models = {}

    def __init__(self, api_key: str = "", **kwargs):
        super().__init__(api_key=api_key, **kwargs)

    async def embeddings(self, texts: List[str], model: str = "BAAI/bge-small-en-v1.5") -> EmbeddingResponse:
        if model not in self._models:
            # Load model in a thread to avoid blocking event loop
            self._models[model] = await asyncio.to_thread(SentenceTransformer, model)
            
        st_model = self._models[model]
        
        # Generate embeddings in a thread
        embeddings = await asyncio.to_thread(st_model.encode, texts)
        
        return EmbeddingResponse(
            embeddings=embeddings.tolist(),
            model=model,
            total_tokens=0,
        )

    async def validate_key(self) -> bool:
        return True
