from typing import List
import google.generativeai as genai
from app.providers.embeddings.base import BaseEmbeddingProvider, EmbeddingResponse

class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    name = "gemini"
    display_name = "Google Gemini"

    def __init__(self, api_key: str = "", **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        genai.configure(api_key=api_key)

    async def embeddings(self, texts: List[str], model: str = "models/text-embedding-004") -> EmbeddingResponse:
        # Gemini expects 'models/' prefix
        if not model.startswith("models/"):
            model = f"models/{model}"
            
        result = genai.embed_content(
            model=model,
            content=texts,
            task_type="retrieval_document",
        )
        
        # Handle both single and multiple texts
        embeddings = result["embedding"]
        if texts and isinstance(texts, list) and len(texts) > 1:
             # Already a list of lists
             pass
        else:
             # Wrap single embedding in a list
             embeddings = [embeddings]

        return EmbeddingResponse(
            embeddings=embeddings,
            model=model,
            total_tokens=0,  # Gemini doesn't return usage for embeddings
        )

    async def validate_key(self) -> bool:
        try:
            # Try a simple embedding to validate key
            genai.embed_content(model="models/text-embedding-004", content="test")
            return True
        except Exception:
            return False
