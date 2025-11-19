from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import asyncio

from ohra.backend.rag.retrieval.vector.retriever import VectorRetriever
from ohra.backend.rag.retrieval.keyword.retriever import BM25Retriever
from ohra.backend.rag.service.v1.schema import RetrievedDocument


@dataclass
class HybridSearchService:
    vector_retriever: VectorRetriever
    keyword_retriever: BM25Retriever
    rrf_k: int = field(default=60)

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        search_mode: str = "hybrid",
    ) -> List[RetrievedDocument]:
        search_methods = {
            "vector": lambda: self.vector_retriever.retrieve(query, top_k, filter),
            "keyword": lambda: self.keyword_retriever.retrieve(query, top_k, filter),
            "hybrid": lambda: self._hybrid_search(query, top_k, filter),
        }

        if search_mode not in search_methods:
            raise ValueError(f"Invalid search_mode: {search_mode}. Must be 'vector', 'keyword', or 'hybrid'")

        return await search_methods[search_mode]()

    async def _hybrid_search(
        self,
        query: str,
        top_k: int,
        filter: Optional[Dict[str, Any]],
    ) -> List[RetrievedDocument]:
        vector_results, keyword_results = await asyncio.gather(
            self.vector_retriever.retrieve(query, top_k * 2, filter),
            self.keyword_retriever.retrieve(query, top_k * 2, filter),
        )

        rrf_scores = defaultdict(float)

        for rank, doc in enumerate(vector_results, 1):
            rrf_scores[doc.id] += 1.0 / (self.rrf_k + rank)

        for rank, doc in enumerate(keyword_results, 1):
            rrf_scores[doc.id] += 1.0 / (self.rrf_k + rank)

        doc_map = {doc.id: doc for doc in [*vector_results, *keyword_results]}

        combined = sorted(
            [
                RetrievedDocument(id=doc_id, score=score, metadata=doc_map[doc_id].metadata)
                for doc_id, score in rrf_scores.items()
            ],
            key=lambda x: x.score,
            reverse=True,
        )[:top_k]

        return combined
