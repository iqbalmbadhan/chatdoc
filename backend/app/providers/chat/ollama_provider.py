from typing import AsyncGenerator, List
import httpx
import json
from app.providers.chat.base import BaseProvider, ChatMessage, ChatResponse, EmbeddingResponse
from app.core.config import settings


class OllamaProvider(BaseProvider):
    name = "ollama"
    display_name = "Ollama (Local)"

    def __init__(self, api_key: str = "", base_url: str = "", **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        self.base_url = base_url or settings.OLLAMA_URL

    async def chat(self, messages: List[ChatMessage], model: str = "llama3", temperature: float = 0.7, max_tokens: int = 2048, **kwargs) -> ChatResponse:
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()

        content = data.get("message", {}).get("content", "")
        total = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)
        return ChatResponse(
            content=content,
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            total_tokens=total,
            model=model,
        )

    async def chat_stream(self, messages: List[ChatMessage], model: str = "llama3", temperature: float = 0.7, max_tokens: int = 2048, **kwargs) -> AsyncGenerator[str, None]:
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            delta = data.get("message", {}).get("content", "")
                            if delta:
                                yield delta
                        except json.JSONDecodeError:
                            pass

    async def embeddings(self, texts: List[str], model: str = "nomic-embed-text") -> EmbeddingResponse:
        embeddings = []
        async with httpx.AsyncClient(timeout=60.0) as client:
            for text in texts:
                response = await client.post(f"{self.base_url}/api/embeddings", json={"model": model, "prompt": text})
                response.raise_for_status()
                embeddings.append(response.json()["embedding"])
        return EmbeddingResponse(embeddings=embeddings, model=model, total_tokens=0)

    async def validate_key(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    def get_available_models(self) -> list:
        return [
            {"id": "llama3", "name": "Llama 3"},
            {"id": "mistral", "name": "Mistral"},
            {"id": "qwen2", "name": "Qwen 2"},
            {"id": "deepseek-r1", "name": "DeepSeek R1"},
            {"id": "nomic-embed-text", "name": "Nomic Embed Text (Embeddings)"},
        ]
