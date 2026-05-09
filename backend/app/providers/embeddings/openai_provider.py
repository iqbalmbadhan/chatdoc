from typing import List
import openai
from app.providers.embeddings.base import BaseEmbeddingProvider, EmbeddingResponse

class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    name = "openai"
    display_name = "OpenAI"

    def __init__(self, api_key: str = "", **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        self.client = openai.AsyncOpenAI(api_key=api_key)

    async def embeddings(self, texts: List[str], model: str = "text-embedding-3-small") -> EmbeddingResponse:
        response = await self.client.embeddings.create(model=model, input=texts)
        return EmbeddingResponse(
            embeddings=[d.embedding for d in response.data],
            model=model,
            total_tokens=response.usage.total_tokens,
        )

    async def validate_key(self) -> bool:
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False
