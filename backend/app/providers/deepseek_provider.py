from typing import AsyncGenerator, List
import openai
from app.providers.base import BaseProvider, ChatMessage, ChatResponse, EmbeddingResponse


class DeepSeekProvider(BaseProvider):
    name = "deepseek"
    display_name = "DeepSeek"

    def __init__(self, api_key: str = "", **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        self.client = openai.AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")

    async def chat(self, messages: List[ChatMessage], model: str = "deepseek-chat", temperature: float = 0.7, max_tokens: int = 2048, **kwargs) -> ChatResponse:
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

    async def chat_stream(self, messages: List[ChatMessage], model: str = "deepseek-chat", temperature: float = 0.7, max_tokens: int = 2048, **kwargs) -> AsyncGenerator[str, None]:
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

    async def embeddings(self, texts: List[str], model: str = "text-embedding-v2") -> EmbeddingResponse:
        # DeepSeek uses OpenAI-compatible embeddings endpoint
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
            {"id": "deepseek-chat", "name": "DeepSeek Chat"},
            {"id": "deepseek-reasoner", "name": "DeepSeek Reasoner (R1)"},
        ]
