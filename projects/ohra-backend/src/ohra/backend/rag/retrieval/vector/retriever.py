from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ohra.shared_kernel.infra.qdrant import QdrantAdapter
from ohra.shared_kernel.infra.sagemaker import SageMakerEmbeddingAdapter
from ohra.backend.rag.service.v1.schema import RetrievedDocument


@dataclass
class VectorRetriever:

    vector_store: QdrantAdapter
    embedding: SageMakerEmbeddingAdapter

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedDocument]:
        query_vector = await self.embedding.embed_text(query)
        results = await self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
            filter=filter,
        )

        return [RetrievedDocument(**result) for result in results]
