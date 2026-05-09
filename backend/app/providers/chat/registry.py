from typing import Dict, Optional, Type
from app.providers.chat.base import BaseProvider
from app.providers.chat.openai_provider import OpenAIProvider
from app.providers.chat.gemini_provider import GeminiProvider
from app.providers.chat.deepseek_provider import DeepSeekProvider
from app.providers.chat.openrouter_provider import OpenRouterProvider
from app.providers.chat.ollama_provider import OllamaProvider

PROVIDER_REGISTRY: Dict[str, Type[BaseProvider]] = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "deepseek": DeepSeekProvider,
    "openrouter": OpenRouterProvider,
    "ollama": OllamaProvider,
}

# Providers that handle chat/completion only — no embedding support
CHAT_ONLY_PROVIDERS = {"openrouter", "deepseek"}



DEFAULT_PROVIDERS = [
    {"name": "openai", "display_name": "OpenAI", "default_model": "gpt-4o-mini", "default_embedding_model": "text-embedding-3-small"},
    {"name": "gemini", "display_name": "Google Gemini", "default_model": "gemini-2.0-flash", "default_embedding_model": "text-embedding-004"},
    {"name": "deepseek", "display_name": "DeepSeek", "default_model": "deepseek-chat", "default_embedding_model": None},
    {"name": "openrouter", "display_name": "OpenRouter", "default_model": "google/gemini-3.1-flash-lite", "default_embedding_model": None},
    {"name": "ollama", "display_name": "Ollama (Local)", "default_model": "llama3", "default_embedding_model": "nomic-embed-text"},
]


def get_provider(name: str, api_key: str = "", **kwargs) -> Optional[BaseProvider]:
    cls = PROVIDER_REGISTRY.get(name)
    if not cls:
        return None
    return cls(api_key=api_key, **kwargs)
