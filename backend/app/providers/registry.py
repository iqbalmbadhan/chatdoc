from typing import Dict, Optional, Type
from app.providers.base import BaseProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.deepseek_provider import DeepSeekProvider
from app.providers.openrouter_provider import OpenRouterProvider
from app.providers.ollama_provider import OllamaProvider

PROVIDER_REGISTRY: Dict[str, Type[BaseProvider]] = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "deepseek": DeepSeekProvider,
    "openrouter": OpenRouterProvider,
    "ollama": OllamaProvider,
}

DEFAULT_PROVIDERS = [
    {"name": "openai", "display_name": "OpenAI", "default_model": "gpt-4o-mini", "default_embedding_model": "text-embedding-3-small"},
    {"name": "gemini", "display_name": "Google Gemini", "default_model": "gemini-1.5-flash", "default_embedding_model": "text-embedding-004"},
    {"name": "deepseek", "display_name": "DeepSeek", "default_model": "deepseek-chat", "default_embedding_model": None},
    {"name": "openrouter", "display_name": "OpenRouter", "default_model": "meta-llama/llama-3.1-8b-instruct:free", "default_embedding_model": None},
    {"name": "ollama", "display_name": "Ollama (Local)", "default_model": "llama3", "default_embedding_model": "nomic-embed-text"},
]


def get_provider(name: str, api_key: str = "", **kwargs) -> Optional[BaseProvider]:
    cls = PROVIDER_REGISTRY.get(name)
    if not cls:
        return None
    return cls(api_key=api_key, **kwargs)
