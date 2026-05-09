from typing import AsyncGenerator, List
import openai
from app.providers.chat.base import BaseProvider, ChatMessage, ChatResponse, EmbeddingResponse

COST_MAP = {
    "gpt-4o": (5.0, 15.0),
    "gpt-4o-mini": (0.15, 0.6),
    "gpt-4-turbo": (10.0, 30.0),
    "gpt-3.5-turbo": (0.5, 1.5),
}


class OpenAIProvider(BaseProvider):
    name = "openai"
    display_name = "OpenAI"

    def __init__(self, api_key: str = "", **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        self.client = openai.AsyncOpenAI(api_key=api_key)

    async def chat(self, messages: List[ChatMessage], model: str = "gpt-4o-mini", temperature: float = 0.7, max_tokens: int = 2048, **kwargs) -> ChatResponse:
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
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            model=model,
            finish_reason=choice.finish_reason or "stop",
        )

    async def chat_stream(self, messages: List[ChatMessage], model: str = "gpt-4o-mini", temperature: float = 0.7, max_tokens: int = 2048, **kwargs) -> AsyncGenerator[str, None]:
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
            total_tokens=response.usage.total_tokens,
        )

    async def validate_key(self) -> bool:
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False

    def get_available_models(self) -> list:
        return [
            {"id": "gpt-4o", "name": "GPT-4o"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
        ]

    @staticmethod
    def estimate_cost(prompt_tokens: int, completion_tokens: int, model: str) -> float:
        if model in COST_MAP:
            inp, out = COST_MAP[model]
            return (prompt_tokens * inp + completion_tokens * out) / 1_000_000
        return 0.0
