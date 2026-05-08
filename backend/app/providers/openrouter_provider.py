from typing import AsyncGenerator, List
import openai
from app.providers.base import BaseProvider, ChatMessage, ChatResponse, EmbeddingResponse


class OpenRouterProvider(BaseProvider):
    name = "openrouter"
    display_name = "OpenRouter"

    def __init__(self, api_key: str = "", **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    async def chat(self, messages: List[ChatMessage], model: str = "meta-llama/llama-3.1-8b-instruct:free", temperature: float = 0.7, max_tokens: int = 2048, **kwargs) -> ChatResponse:
        response = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        usage = response.usage
        return ChatResponse(
            content=choice.message.content or "",
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            model=model,
        )

    async def chat_stream(self, messages: List[ChatMessage], model: str = "meta-llama/llama-3.1-8b-instruct:free", temperature: float = 0.7, max_tokens: int = 2048, **kwargs) -> AsyncGenerator[str, None]:
        stream = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta

    async def embeddings(self, texts: List[str], model: str = "text-embedding-3-small") -> EmbeddingResponse:
        response = await self.client.embeddings.create(model=model, input=texts)
        return EmbeddingResponse(
            embeddings=[d.embedding for d in response.data],
            model=model,
            total_tokens=response.usage.total_tokens if response.usage else 0,
        )

    async def validate_key(self) -> bool:
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False

    def get_available_models(self) -> list:
        return [
            {"id": "meta-llama/llama-3.1-8b-instruct:free", "name": "Llama 3.1 8B (Free)"},
            {"id": "mistralai/mistral-7b-instruct:free", "name": "Mistral 7B (Free)"},
            {"id": "google/gemma-2-9b-it:free", "name": "Gemma 2 9B (Free)"},
            {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet"},
            {"id": "openai/gpt-4o", "name": "GPT-4o"},
        ]
