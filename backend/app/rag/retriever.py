from typing import List, Optional, Dict, Any
import structlog

from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore
from app.core.config import settings

logger = structlog.get_logger()


class RAGRetriever:
    def __init__(self, embedding_model: str = None, top_k: int = None):
        self.embedding_model = embedding_model or settings.DEFAULT_EMBEDDING_MODEL
        self.top_k = top_k or settings.DEFAULT_TOP_K
        self.vector_store = VectorStore()

    async def retrieve(
        self,
        query: str,
        provider=None,
        doc_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        query_embedding = await EmbeddingService.embed_texts(
            texts=[query],
            provider=provider,
            model=self.embedding_model,
        )
        results = await self.vector_store.search(
            query_embedding=query_embedding[0],
            top_k=self.top_k,
            doc_ids=doc_ids,
        )
        return results

    def build_context(self, retrieved: List[Dict]) -> str:
        if not retrieved:
            return ""
        parts = []
        for i, r in enumerate(retrieved, 1):
            filename = r.get("filename", "unknown")
            text = r.get("text", "")
            parts.append(f"[Source {i}: {filename}]\n{text}")
        return "\n\n---\n\n".join(parts)

    def build_prompt(self, query: str, context: str, system_prompt: Optional[str] = None) -> List[Dict]:
        sys_content = system_prompt or (
            "You are a helpful AI assistant. Answer questions based on the provided documents. "
            "Always cite the source document when referring to specific information. "
            "If the answer is not in the documents, say so clearly."
        )
        messages = [{"role": "system", "content": sys_content}]

        if context:
            messages.append({
                "role": "user",
                "content": f"Context from documents:\n\n{context}\n\n---\n\nQuestion: {query}"
            })
        else:
            messages.append({"role": "user", "content": query})

        return messages
