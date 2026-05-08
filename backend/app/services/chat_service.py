import uuid
import time
from datetime import datetime, timezone
from typing import Optional, AsyncGenerator, List


def _safe_uuid(value: Optional[str]) -> Optional[uuid.UUID]:
    if not value:
        return None
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        return None

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.models.chat import Conversation, Message
from app.models.document import Document
from app.rag.retriever import RAGRetriever
from app.providers.registry import get_provider
from app.providers.base import ChatMessage
from app.services.provider_service import ProviderService
from app.services.analytics_service import AnalyticsService

logger = structlog.get_logger()


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_conversation(
        self,
        conversation_id: Optional[uuid.UUID],
        session_id: Optional[str],
        user_id: Optional[str],
        title: str = None,
    ) -> Conversation:
        if conversation_id:
            result = await self.db.execute(select(Conversation).where(Conversation.id == conversation_id))
            conv = result.scalar_one_or_none()
            if conv:
                return conv

        try:
            uid = uuid.UUID(user_id) if user_id else None
        except (ValueError, AttributeError):
            uid = None
        conv = Conversation(
            title=title or "New Conversation",
            user_id=uid,
            session_id=session_id,
        )
        self.db.add(conv)
        await self.db.commit()
        await self.db.refresh(conv)
        return conv

    async def get_conversation_history(self, conversation_id: uuid.UUID, limit: int = 10) -> List[ChatMessage]:
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        messages = list(reversed(result.scalars().all()))
        return [ChatMessage(role=m.role, content=m.content) for m in messages]

    async def chat(
        self,
        query: str,
        conversation_id: Optional[uuid.UUID] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
        visitor_id: Optional[str] = None,
    ) -> dict:
        start_time = time.time()

        conv = await self.get_or_create_conversation(conversation_id, session_id, user_id, title=query[:60])

        # Save user message
        user_msg = Message(conversation_id=conv.id, role="user", content=query)
        self.db.add(user_msg)

        # Determine provider and model
        provider_config, api_key = await ProviderService(self.db).get_default_provider()
        provider_name = provider_name or (provider_config.name if provider_config else "ollama")
        model_name = model_name or (provider_config.default_model if provider_config else "llama3")

        provider = get_provider(provider_name, api_key=api_key or "")

        # RAG retrieval
        retriever = RAGRetriever()
        retrieved = await retriever.retrieve(query, provider=None)
        context = retriever.build_context(retrieved)
        messages_raw = retriever.build_prompt(query, context)

        # Build messages: system prompt → conversation history → current user turn
        history = await self.get_conversation_history(conv.id, limit=8)
        system_msg = ChatMessage(role=messages_raw[0]["role"], content=messages_raw[0]["content"])
        user_content = messages_raw[-1]["content"]  # includes injected context when available
        messages = [system_msg, *history, ChatMessage(role="user", content=user_content)]

        # Call AI
        response = await provider.chat(messages=messages, model=model_name)
        latency_ms = int((time.time() - start_time) * 1000)

        # Format source documents
        source_docs = [
            {
                "doc_id": r["doc_id"],
                "filename": r.get("filename", ""),
                "chunk_index": r.get("chunk_index"),
                "score": round(r.get("score", 0), 3),
                "excerpt": r.get("text", "")[:200],
            }
            for r in retrieved
        ]

        # Estimate cost
        from app.providers.openai_provider import OpenAIProvider
        cost = OpenAIProvider.estimate_cost(response.prompt_tokens, response.completion_tokens, model_name)

        # Save assistant message
        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=response.content,
            provider=provider_name,
            model=model_name,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens,
            estimated_cost=cost,
            latency_ms=latency_ms,
            source_documents=source_docs,
            retrieval_count=len(retrieved),
            visitor_id=_safe_uuid(visitor_id),
        )
        self.db.add(assistant_msg)

        conv.message_count = (conv.message_count or 0) + 2
        await self.db.commit()
        await self.db.refresh(assistant_msg)

        # Track usage
        await AnalyticsService(self.db).record_usage(
            provider=provider_name,
            model=model_name,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            cost=cost,
            latency_ms=latency_ms,
        )

        return {
            "conversation_id": conv.id,
            "message": assistant_msg,
        }

    async def chat_stream(
        self,
        query: str,
        conversation_id: Optional[uuid.UUID] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        provider_name: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        conv = await self.get_or_create_conversation(conversation_id, session_id, user_id, title=query[:60])

        provider_config, api_key = await ProviderService(self.db).get_default_provider()
        provider_name = provider_name or (provider_config.name if provider_config else "ollama")
        model_name = model_name or (provider_config.default_model if provider_config else "llama3")

        provider = get_provider(provider_name, api_key=api_key or "")

        retriever = RAGRetriever()
        retrieved = await retriever.retrieve(query)
        context = retriever.build_context(retrieved)
        messages_raw = retriever.build_prompt(query, context)
        messages = [ChatMessage(role=m["role"], content=m["content"]) for m in messages_raw]

        full_response = ""
        async for token in provider.chat_stream(messages=messages, model=model_name):
            full_response += token
            yield token

        # Save conversation after streaming completes
        user_msg = Message(conversation_id=conv.id, role="user", content=query)
        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=full_response,
            provider=provider_name,
            model=model_name,
        )
        self.db.add(user_msg)
        self.db.add(assistant_msg)
        conv.message_count = (conv.message_count or 0) + 2
        await self.db.commit()

    async def list_conversations(self, user_id: Optional[str] = None, session_id: Optional[str] = None, page: int = 1, page_size: int = 20) -> tuple:
        query = select(Conversation).where(Conversation.is_active == True)
        uid = _safe_uuid(user_id)
        if uid:
            query = query.where(Conversation.user_id == uid)
        elif session_id:
            query = query.where(Conversation.session_id == session_id)
        query = query.order_by(desc(Conversation.updated_at))

        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        result = await self.db.execute(query.offset((page - 1) * page_size).limit(page_size))
        return result.scalars().all(), total

    async def get_conversation_messages(self, conversation_id: uuid.UUID) -> List[Message]:
        result = await self.db.execute(
            select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
        )
        return result.scalars().all()
