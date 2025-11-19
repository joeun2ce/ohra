from collections import defaultdict
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
import logging

from ohra.shared_kernel.infra.vector_store.exceptions import VectorStoreException

logger = logging.getLogger(__name__)


class QdrantAdapter:
    def __init__(self, host: str, port: int, collection_name: str):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name

    async def create_collection(self, collection_name: str, vector_size: int, enable_sparse: bool = True) -> None:
        try:
            vectors_config = {"dense": VectorParams(size=vector_size, distance=Distance.COSINE)}

            sparse_vectors_config = {"sparse": SparseVectorParams()} if enable_sparse else None

            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=vectors_config,
                sparse_vectors_config=sparse_vectors_config,
            )
        except Exception as e:
            raise VectorStoreException(f"Failed to create collection: {e}") from e

    async def ensure_collection_exists(self, vector_size: int, enable_sparse: bool = True) -> None:
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

        must_conditions = [FieldCondition(key=key, match=MatchValue(value=value)) for key, value in filter.items()]
        return Filter(must=must_conditions) if must_conditions else None

    def _apply_rrf(self, dense_results, sparse_results, top_k: int, k: int = 60):
        """
        Reciprocal Rank Fusion (RRF) 구현

        RRF score = sum(1 / (k + rank)) for each retriever

        Args:
            dense_results: Dense vector 검색 결과
            sparse_results: Sparse vector 검색 결과
            top_k: 반환할 최대 문서 수
            k: RRF 상수 (기본값: 60)
        """
        rrf_scores = defaultdict(float)
        doc_map = {}

        for rank, hit in enumerate(dense_results, start=1):
            doc_id = hit.id
            rrf_scores[doc_id] += 1.0 / (k + rank)
            if doc_id not in doc_map:
                doc_map[doc_id] = hit

        for rank, hit in enumerate(sparse_results, start=1):
            doc_id = hit.id
            rrf_scores[doc_id] += 1.0 / (k + rank)
            if doc_id not in doc_map:
                doc_map[doc_id] = hit

        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for doc_id, rrf_score in sorted_docs[:top_k]:
            hit = doc_map[doc_id]
            hit.score = rrf_score
            results.append(hit)

        return results

    async def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        query_sparse_vector: Optional[Dict[str, List]] = None,
        fusion: str = "rrf",
    ) -> List[Dict[str, Any]]:
        """
        벡터 검색 수행 (Dense-only 또는 Hybrid with RRF)

        Qdrant 1.16+에서 sparse vector 검색을 지원합니다.

        Args:
            query_vector: Dense 쿼리 벡터
            top_k: 반환할 최대 문서 수
            filter: 메타데이터 필터
            query_sparse_vector: Sparse 벡터 (Hybrid 검색 시)
            fusion: Fusion 방법 (기본값: "rrf")

        Returns:
            검색 결과 리스트
        """
        try:
            search_filter = self._build_filter(filter)

            if query_sparse_vector:
                logger.info(f"Hybrid search: top_k={top_k}, sparse_indices={len(query_sparse_vector['indices'])}")

                dense_results = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    using="dense",
                    limit=top_k * 2,
                    query_filter=search_filter,
                ).points
                logger.info(f"Dense search returned {len(dense_results)} results")

                sparse_results = self.client.query_points(
                    collection_name=self.collection_name,
                    query=SparseVector(
                        indices=query_sparse_vector["indices"],
                        values=query_sparse_vector["values"],
                    ),
                    using="sparse",
                    limit=top_k * 2,
                    query_filter=search_filter,
                ).points
                logger.info(f"Sparse search returned {len(sparse_results)} results")

                results = self._apply_rrf(dense_results, sparse_results, top_k)
                logger.info(f"RRF returned {len(results)} results")
            else:
                logger.info(f"Dense-only search: top_k={top_k}")
                results = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    using="dense",
                    limit=top_k,
                    query_filter=search_filter,
                ).points
                logger.info(f"Dense search returned {len(results)} results")

            return [{"id": hit.id, "score": hit.score, "metadata": hit.payload} for hit in results]
        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
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

    async def get_all_by_filter(self, filter: Dict[str, Any], batch_size: int = 1000) -> List[Dict[str, Any]]:
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
