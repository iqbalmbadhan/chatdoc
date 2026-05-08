from typing import List, Optional, Dict, Any
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter,
    FieldCondition, MatchValue, MatchAny, FilterSelector,
)
import structlog
import uuid

from app.core.config import settings

logger = structlog.get_logger()

_async_client: Optional[AsyncQdrantClient] = None


def get_qdrant_client() -> AsyncQdrantClient:
    global _async_client
    if _async_client is None:
        _async_client = AsyncQdrantClient(url=settings.QDRANT_URL)
    return _async_client


class VectorStore:
    def __init__(self, collection_name: str = None):
        self.collection_name = collection_name or settings.QDRANT_COLLECTION
        self.client = get_qdrant_client()

    async def ensure_collection(self, dimension: int = 384):
        collections = await self.client.get_collections()
        names = [c.name for c in collections.collections]
        if self.collection_name not in names:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            )
            logger.info("Created Qdrant collection", name=self.collection_name, dim=dimension)

    async def upsert_chunks(
        self,
        doc_id: str,
        chunks: List[str],
        embeddings: List[List[float]],
        metadata: Dict[str, Any] = None,
    ):
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_id}_{i}"))
            payload = {
                "doc_id": doc_id,
                "chunk_index": i,
                "text": chunk,
                **(metadata or {}),
            }
            points.append(PointStruct(id=point_id, vector=embedding, payload=payload))

        await self.client.upsert(collection_name=self.collection_name, points=points)
        logger.info("Upserted chunks", doc_id=doc_id, count=len(points))

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        doc_ids: Optional[List[str]] = None,
    ) -> List[Dict]:
        search_filter = None
        if doc_ids:
            # MatchAny filters by multiple values; MatchValue is for a single value
            search_filter = Filter(
                must=[FieldCondition(key="doc_id", match=MatchAny(any=doc_ids))]
            )

        results = await self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=search_filter,
            with_payload=True,
        )

        return [
            {
                "doc_id": r.payload.get("doc_id"),
                "text": r.payload.get("text"),
                "chunk_index": r.payload.get("chunk_index"),
                "filename": r.payload.get("filename"),
                "score": r.score,
            }
            for r in results
        ]

    async def delete_document(self, doc_id: str):
        # FilterSelector wraps a Filter for use in point deletion operations
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
                )
            ),
        )
        logger.info("Deleted document vectors", doc_id=doc_id)

    async def get_collection_info(self) -> dict:
        try:
            info = await self.client.get_collection(self.collection_name)
            return {
                "points_count": info.points_count,
                "status": info.status.value if hasattr(info.status, "value") else str(info.status),
            }
        except Exception:
            return {"points_count": 0, "status": "not_initialized"}
