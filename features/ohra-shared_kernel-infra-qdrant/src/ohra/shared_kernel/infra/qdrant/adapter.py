from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    SparseVectorParams,
    SparseVector,
    FieldCondition,
    MatchValue,
)
from typing import List, Dict, Any, Optional, Union
from ohra.shared_kernel.infra.vector_store.exceptions import VectorStoreException


class QdrantAdapter:
    def __init__(self, host: str, port: int, collection_name: str):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name

    async def create_collection(
        self, collection_name: str, vector_size: int, enable_sparse: bool = True
    ) -> None:
        try:
            # Named vector configuration
            vectors_config = {"dense": VectorParams(size=vector_size, distance=Distance.COSINE)}

            sparse_vectors_config = {"sparse": SparseVectorParams()} if enable_sparse else None

            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=vectors_config,
                sparse_vectors_config=sparse_vectors_config,
            )
        except Exception as e:
            raise VectorStoreException(f"Failed to create collection: {e}") from e

    async def ensure_collection_exists(
        self, vector_size: int, enable_sparse: bool = True
    ) -> None:
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                await self.create_collection(self.collection_name, vector_size, enable_sparse)
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                return
            raise VectorStoreException(f"Failed to ensure collection exists: {e}") from e

    async def upsert(
        self,
        id: Union[str, int],
        vector: List[float],
        metadata: Dict[str, Any],
        sparse_vector: Optional[Dict[str, List]] = None,
    ) -> None:
        try:
            # Build vector dict with dense and sparse vectors
            vector_dict = {"dense": vector}
            if sparse_vector:
                vector_dict["sparse"] = SparseVector(
                    indices=sparse_vector["indices"],
                    values=sparse_vector["values"],
                )

            point = PointStruct(
                id=id,
                vector=vector_dict,
                payload=metadata,
            )
            self.client.upsert(collection_name=self.collection_name, points=[point])
        except Exception as e:
            raise VectorStoreException(f"Failed to upsert vector: {e}") from e

    async def upsert_batch(self, vectors: List[Dict[str, Any]]) -> None:
        try:
            points = []
            for vec in vectors:
                vector_dict = {"dense": vec["vector"]}

                if "sparse_vector" in vec and vec["sparse_vector"]:
                    vector_dict["sparse"] = SparseVector(
                        indices=vec["sparse_vector"]["indices"],
                        values=vec["sparse_vector"]["values"],
                    )

                points.append(
                    PointStruct(
                        id=vec["id"],
                        vector=vector_dict,
                        payload=vec["metadata"],
                    )
                )

            self.client.upsert(collection_name=self.collection_name, points=points)
        except Exception as e:
            raise VectorStoreException(f"Failed to batch upsert vectors: {e}") from e

    def _build_filter(self, filter: Optional[Dict[str, Any]]) -> Optional[Filter]:
        if not filter:
            return None

        must_conditions = [
            FieldCondition(key=key, match=MatchValue(value=value))
            for key, value in filter.items()
        ]
        return Filter(must=must_conditions) if must_conditions else None

    async def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        query_sparse_vector: Optional[Dict[str, List]] = None,
        fusion: str = "rrf",
    ) -> List[Dict[str, Any]]:
        try:
            search_filter = self._build_filter(filter)
            # Hybrid search with named vectors
            if query_sparse_vector:
                results = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    using="dense",
                    prefetch=[
                        {
                            "query": SparseVector(
                                indices=query_sparse_vector["indices"],
                                values=query_sparse_vector["values"],
                            ),
                            "using": "sparse",
                            "limit": top_k * 2,
                        }
                    ],
                    limit=top_k,
                    query_filter=search_filter,
                ).points
            else:
                # Dense-only search with named vector
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=("dense", query_vector),
                    limit=top_k,
                    query_filter=search_filter,
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
            result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=self._build_filter(filter),
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
            result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=self._build_filter(filter),
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
            points, _ = result
            return [{"id": point.id, "metadata": point.payload} for point in points]
        except Exception as e:
            raise VectorStoreException(f"Failed to get by filter: {e}") from e

    async def get_all_by_filter(
        self, filter: Dict[str, Any], batch_size: int = 1000
    ) -> List[Dict[str, Any]]:
        try:
            all_points = []
            offset = None

            while True:
                result = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=self._build_filter(filter),
                    limit=batch_size,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False,
                )
                points, next_offset = result
                all_points.extend([{"id": point.id, "metadata": point.payload} for point in points])

                if next_offset is None or len(points) == 0:
                    break

                offset = next_offset

            return all_points
        except Exception as e:
            raise VectorStoreException(f"Failed to get all by filter: {e}") from e

    async def delete_by_filter(self, filter: Dict[str, Any]) -> None:
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=self._build_filter(filter),
            )
        except Exception as e:
            raise VectorStoreException(f"Failed to delete by filter: {e}") from e
