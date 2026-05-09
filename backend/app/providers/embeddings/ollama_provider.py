from typing import List
import httpx
from app.providers.embeddings.base import BaseEmbeddingProvider, EmbeddingResponse

class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    name = "ollama"
    display_name = "Ollama"

    def __init__(self, api_key: str = "", **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        self.base_url = kwargs.get("base_url", "http://ollama:11434")

    async def embeddings(self, texts: List[str], model: str) -> EmbeddingResponse:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/embed",
                json={"model": model, "input": texts},
            )
            response.raise_for_status()
            data = response.json()
            
            return EmbeddingResponse(
                embeddings=data["embeddings"],
                model=model,
                total_tokens=0,
            )

    async def validate_key(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
