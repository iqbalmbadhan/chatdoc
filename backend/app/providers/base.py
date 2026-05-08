from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Optional
from dataclasses import dataclass


@dataclass
class ChatMessage:
    role: str  # system / user / assistant
    content: str


@dataclass
class ChatResponse:
    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    finish_reason: str = "stop"


@dataclass
class EmbeddingResponse:
    embeddings: List[List[float]]
    model: str
    total_tokens: int


class BaseProvider(ABC):
    name: str = "base"
    display_name: str = "Base Provider"

    def __init__(self, api_key: str = "", base_url: str = "", **kwargs):
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> ChatResponse:
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    async def embeddings(
        self,
        texts: List[str],
        model: str,
    ) -> EmbeddingResponse:
        pass

    @abstractmethod
    async def validate_key(self) -> bool:
        pass

    def get_available_models(self) -> List[dict]:
        return []

    @staticmethod
    def estimate_cost(prompt_tokens: int, completion_tokens: int, model: str) -> float:
        return 0.0
