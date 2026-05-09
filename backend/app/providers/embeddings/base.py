from typing import List
from pydantic import BaseModel

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    model: str
    total_tokens: int

class BaseEmbeddingProvider:
    name: str = ""
    display_name: str = ""

    def __init__(self, api_key: str = "", **kwargs):
        self.api_key = api_key
        self.kwargs = kwargs

    async def embeddings(self, texts: List[str], model: str) -> EmbeddingResponse:
        raise NotImplementedError

    async def validate_key(self) -> bool:
        return True
