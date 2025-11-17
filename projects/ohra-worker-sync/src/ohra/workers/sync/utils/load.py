import logging
from typing import List, Dict, Any
from ohra.shared_kernel.infra.qdrant import QdrantAdapter

logger = logging.getLogger(__name__)


async def load_batch(vectors: List[Dict[str, Any]], vector_store: QdrantAdapter) -> int:
    try:
        unique_vectors = []
        for vec in vectors:
            content_hash = vec["metadata"].get("hash")
            if content_hash:
                exists = await vector_store.exists({"hash": content_hash})
                if exists:
                    continue
            unique_vectors.append(vec)

        if unique_vectors:
            await vector_store.upsert_batch(unique_vectors)

        return len(unique_vectors)
    except Exception as e:
        logger.error(f"Failed to load batch: {e}", exc_info=True)
        return 0
