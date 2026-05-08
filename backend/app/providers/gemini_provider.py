from typing import AsyncGenerator, List
import httpx
import json
from app.providers.base import BaseProvider, ChatMessage, ChatResponse, EmbeddingResponse

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GeminiProvider(BaseProvider):
    name = "gemini"
    display_name = "Google Gemini"

    async def chat(self, messages: List[ChatMessage], model: str = "gemini-1.5-flash", temperature: float = 0.7, max_tokens: int = 2048, **kwargs) -> ChatResponse:
        contents = []
        system_instruction = None
        for m in messages:
            if m.role == "system":
                system_instruction = {"parts": [{"text": m.content}]}
            else:
                role = "user" if m.role == "user" else "model"
                contents.append({"role": role, "parts": [{"text": m.content}]})

        payload: dict = {
            "contents": contents,
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{GEMINI_BASE}/models/{model}:generateContent?key={self.api_key}",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = data["candidates"][0]["content"]["parts"][0]["text"]
        usage = data.get("usageMetadata", {})
        return ChatResponse(
            content=content,
            prompt_tokens=usage.get("promptTokenCount", 0),
            completion_tokens=usage.get("candidatesTokenCount", 0),
            total_tokens=usage.get("totalTokenCount", 0),
            model=model,
        )

    async def chat_stream(self, messages: List[ChatMessage], model: str = "gemini-1.5-flash", temperature: float = 0.7, max_tokens: int = 2048, **kwargs) -> AsyncGenerator[str, None]:
        contents = [{"role": "user" if m.role == "user" else "model", "parts": [{"text": m.content}]} for m in messages if m.role != "system"]
        payload = {"contents": contents, "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}}

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", f"{GEMINI_BASE}/models/{model}:streamGenerateContent?key={self.api_key}&alt=sse", json=payload) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        try:
                            data = json.loads(line[5:])
                            text = data["candidates"][0]["content"]["parts"][0]["text"]
                            if text:
                                yield text
                        except Exception:
                            pass

    async def embeddings(self, texts: List[str], model: str = "text-embedding-004") -> EmbeddingResponse:
        embeddings = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for text in texts:
                response = await client.post(
                    f"{GEMINI_BASE}/models/{model}:embedContent?key={self.api_key}",
                    json={"model": f"models/{model}", "content": {"parts": [{"text": text}]}},
                )
                response.raise_for_status()
                embeddings.append(response.json()["embedding"]["values"])
        return EmbeddingResponse(embeddings=embeddings, model=model, total_tokens=0)

    async def validate_key(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{GEMINI_BASE}/models?key={self.api_key}")
                return r.status_code == 200
        except Exception:
            return False

    def get_available_models(self) -> list:
        return [
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash"},
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro"},
            {"id": "gemini-2.0-flash-exp", "name": "Gemini 2.0 Flash (Exp)"},
        ]
