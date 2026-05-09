import google.generativeai as genai
from typing import AsyncGenerator, List
from app.providers.chat.base import BaseProvider, ChatMessage, ChatResponse, EmbeddingResponse


class GeminiProvider(BaseProvider):
    name = "gemini"
    display_name = "Google Gemini"

    def __init__(self, api_key: str = "", **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        genai.configure(api_key=api_key)

    async def chat(self, messages: List[ChatMessage], model: str = "gemini-2.0-flash", temperature: float = 0.7, max_tokens: int = 2048, **kwargs) -> ChatResponse:
        system_instruction = None
        history = []
        
        for m in messages[:-1]:
            if m.role == "system":
                system_instruction = m.content
            else:
                role = "user" if m.role == "user" else "model"
                history.append({"role": role, "parts": [m.content]})
        
        last_msg = messages[-1].content
        
        gen_model = genai.GenerativeModel(
            model_name=model,
            system_instruction=system_instruction
        )
        
        chat = gen_model.start_chat(history=history)
        response = await chat.send_message_async(
            last_msg,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
        )
        
        return ChatResponse(
            content=response.text,
            prompt_tokens=0, # SDK doesn't expose this easily in a single call without count_tokens
            completion_tokens=0,
            total_tokens=0,
            model=model,
        )

    async def chat_stream(self, messages: List[ChatMessage], model: str = "gemini-2.0-flash", temperature: float = 0.7, max_tokens: int = 2048, **kwargs) -> AsyncGenerator[str, None]:
        system_instruction = None
        history = []
        
        for m in messages[:-1]:
            if m.role == "system":
                system_instruction = m.content
            else:
                role = "user" if m.role == "user" else "model"
                history.append({"role": role, "parts": [m.content]})
        
        last_msg = messages[-1].content
        
        gen_model = genai.GenerativeModel(
            model_name=model,
            system_instruction=system_instruction
        )
        
        chat = gen_model.start_chat(history=history)
        response = await chat.send_message_async(
            last_msg,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            ),
            stream=True
        )
        
        async for chunk in response:
            if chunk.text:
                yield chunk.text

    async def embeddings(self, texts: List[str], model: str = "models/text-embedding-004") -> EmbeddingResponse:
        result = genai.embed_content(
            model=model,
            content=texts,
            task_type="retrieval_document"
        )
        return EmbeddingResponse(
            embeddings=result["embedding"],
            model=model,
            total_tokens=0
        )

    async def validate_key(self) -> bool:
        try:
            # Just try to list models
            genai.list_models()
            return True
        except Exception:
            return False

    def get_available_models(self) -> list:
        return [
            {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash"},
            {"id": "gemini-2.0-flash-lite", "name": "Gemini 2.0 Flash Lite"},
            {"id": "gemini-flash-latest", "name": "Gemini Flash Latest"},
            {"id": "gemini-pro-latest", "name": "Gemini Pro Latest"},
        ]

