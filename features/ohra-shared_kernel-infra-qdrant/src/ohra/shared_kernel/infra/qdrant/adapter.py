from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter
from typing import List, Dict, Any, Optional
from ohra.shared_kernel.infra.vector_store.exceptions import VectorStoreException


class QdrantAdapter:
    def __init__(self, host: str, port: int, collection_name: str):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name

    async def create_collection(self, collection_name: str, vector_size: int) -> None:
        try:
            self.client.create_collection(
                collection_name=collection_name, vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
        except Exception as e:
            raise VectorStoreException(f"Failed to create collection: {e}") from e

    async def ensure_collection_exists(self, vector_size: int) -> None:
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                return
            raise VectorStoreException(f"Failed to ensure collection exists: {e}") from e

    async def upsert(self, id: str, vector: List[float], metadata: Dict[str, Any]) -> None:
        try:
            point = PointStruct(id=id, vector=vector, payload=metadata)
            self.client.upsert(collection_name=self.collection_name, points=[point])
        except Exception as e:
            raise VectorStoreException(f"Failed to upsert vector: {e}") from e

    async def upsert_batch(self, vectors: List[Dict[str, Any]]) -> None:
        try:
            points = [PointStruct(id=vec["id"], vector=vec["vector"], payload=vec["metadata"]) for vec in vectors]
            self.client.upsert(collection_name=self.collection_name, points=points)
        except Exception as e:
            raise VectorStoreException(f"Failed to batch upsert vectors: {e}") from e

    async def search(
        self, query_vector: List[float], top_k: int = 5, filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        try:
            search_filter = Filter(**filter) if filter else None
            results = self.client.search(
                collection_name=self.collection_name, query_vector=query_vector, limit=top_k, query_filter=search_filter
            )
            return [{"id": hit.id, "score": hit.score, "metadata": hit.payload} for hit in results]
        except Exception as e:
            raise VectorStoreException(f"Failed to search vectors: {e}") from e

    async def delete(self, ids: List[str]) -> None:
        try:
            self.client.delete(collection_name=self.collection_name, points_selector=ids)
        except Exception as e:
            raise VectorStoreException(f"Failed to delete vectors: {e}") from e

    async def exists(self, filter: Dict[str, Any]) -> bool:
        try:
            from qdrant_client.models import FieldCondition, MatchValue
            import logging

            logger = logging.getLogger(__name__)
            must_conditions = [FieldCondition(key=key, match=MatchValue(value=value)) for key, value in filter.items()]
            result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(must=must_conditions) if must_conditions else None,
                limit=1,
                with_payload=False,
                with_vectors=False,
            )
            points, _ = result
            return len(points) > 0
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to check existence: {e}")
            return False

    async def get_by_filter(self, filter: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        try:
            from qdrant_client.models import FieldCondition, MatchValue

            must_conditions = [FieldCondition(key=key, match=MatchValue(value=value)) for key, value in filter.items()]
            result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(must=must_conditions) if must_conditions else None,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
            points, _ = result
            return [{"id": point.id, "metadata": point.payload} for point in points]
        except Exception as e:
            raise VectorStoreException(f"Failed to get by filter: {e}") from e

    async def delete_by_filter(self, filter: Dict[str, Any]) -> None:
        try:
            from qdrant_client.models import FieldCondition, MatchValue

            must_conditions = [FieldCondition(key=key, match=MatchValue(value=value)) for key, value in filter.items()]
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(must=must_conditions) if must_conditions else None,
            )
        except Exception as e:
            raise VectorStoreException(f"Failed to delete by filter: {e}") from e
