from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from collections import Counter

from ohra.shared_kernel.infra.qdrant import QdrantAdapter
from ohra.shared_kernel.infra.sagemaker import SageMakerEmbeddingAdapter
from ohra.backend.rag.service.v1.schema import RetrievedDocument


def _tokenize_korean_for_sparse(text: str) -> List[str]:
    tokens = []
    words = text.lower().split()

    for word in words:
        tokens.append(word)
        if len(word) >= 2:
            for i in range(len(word) - 1):
                if i + 2 <= len(word):
                    tokens.append(word[i : i + 2])
                if i + 3 <= len(word):
                    tokens.append(word[i : i + 3])

    return tokens


@dataclass
class HybridRetriever:
    vector_store: QdrantAdapter
    embedding: SageMakerEmbeddingAdapter

    def _calculate_query_sparse_vector(self, query: str) -> Dict[str, List[int]]:
        tokens = _tokenize_korean_for_sparse(query)
        if not tokens:
            return {"indices": [], "values": []}

        token_counts = Counter(tokens)
        total_tokens = len(tokens)

        indices = []
        values = []

        for token, count in token_counts.items():
            token_id = hash(token) % (2**31)
            score = count / total_tokens
            indices.append(token_id)
            values.append(float(score))

        return {"indices": indices, "values": values}

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        search_mode: str = "hybrid",
    ) -> List[RetrievedDocument]:
        query_vector = await self.embedding.embed_text(query)

        if search_mode == "hybrid":
            query_sparse_vector = self._calculate_query_sparse_vector(query)
            results = await self.vector_store.search(
                query_vector=query_vector,
                top_k=top_k,
                filter=filter,
                query_sparse_vector=query_sparse_vector,
                fusion="rrf",
            )
        else:
            results = await self.vector_store.search(
                query_vector=query_vector,
                top_k=top_k,
                filter=filter,
            )

        documents = [RetrievedDocument(**result) for result in results]
        return documents
