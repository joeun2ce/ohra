from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import logging

from rank_bm25 import BM25Okapi
from ohra.shared_kernel.infra.qdrant import QdrantAdapter
from ohra.backend.rag.service.v1.schema import RetrievedDocument

logger = logging.getLogger(__name__)


def _tokenize_korean(text: str) -> List[str]:
    # 단순 단어
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
class BM25Retriever:
    vector_store: QdrantAdapter
    _bm25_index: Optional[BM25Okapi] = field(default=None, init=False, repr=False)
    _documents: List[Dict[str, Any]] = field(default_factory=list, init=False, repr=False)

    async def _build_index(self) -> None:
        if self._bm25_index is not None:
            return

        logger.info("Building BM25 index from Qdrant documents...")
        all_docs = await self.vector_store.get_all_by_filter(filter={}, batch_size=1000)

        if not all_docs:
            logger.warning("No documents found in Qdrant for BM25 indexing")
            self._documents = []
            self._bm25_index = BM25Okapi([[]])
            return

        self._documents = all_docs
        tokenized_docs = [_tokenize_korean(doc.get("metadata", {}).get("content", "")) for doc in all_docs]

        self._bm25_index = BM25Okapi(tokenized_docs)
        logger.info(f"BM25 index built with {len(self._documents)} documents")

    def _matches_filter(self, metadata: Dict[str, Any], filter: Dict[str, Any]) -> bool:
        return all(metadata.get(k) == v for k, v in filter.items())

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedDocument]:
        await self._build_index()

        if not self._documents:
            return []

        query_tokens = _tokenize_korean(query)
        scores = self._bm25_index.get_scores(query_tokens)
        scored_docs = sorted(zip(scores, self._documents), key=lambda x: x[0], reverse=True)

        if filter:
            scored_docs = [
                (score, doc) for score, doc in scored_docs if self._matches_filter(doc.get("metadata", {}), filter)
            ]

        documents = [
            RetrievedDocument(id=doc["id"], score=float(score), metadata=doc.get("metadata", {}))
            for score, doc in scored_docs[:top_k]
            if score > 0
        ]
        return documents
