import hashlib
from typing import List, Dict, Any
from collections import Counter
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ohra.shared_kernel.infra.sagemaker import SageMakerEmbeddingAdapter
from ohra.workers.sync.schemas import VectorPayload


def _calculate_sparse_vector(text: str) -> Dict[str, List]:
    tokens = text.lower().split()
    if not tokens:
        return {"indices": [], "values": []}

    token_counts = Counter(tokens)
    total_tokens = len(tokens)

    indices = []
    values = []

    for token, count in token_counts.items():
        token_id = hash(token) % (2 ** 31)
        score = count / total_tokens
        indices.append(token_id)
        values.append(float(score))

    return {"indices": indices, "values": values}


async def transform_batch(
    source_type: str,
    documents: List[Dict[str, Any]],
    embedding: SageMakerEmbeddingAdapter,
    chunk_size: int = 1500,
    chunk_overlap: int = 300,
) -> List[Dict[str, Any]]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    chunks = []
    for doc in documents:
        texts = splitter.split_text(doc.get("content", ""))
        for i, text in enumerate(texts):
            if len(text.strip()) >= 50:
                chunks.append(
                    {
                        "chunk": {
                            "id": f"{doc['id']}_chunk_{i}",
                            "document_id": doc["id"],
                            "chunk_index": i,
                            "content": text.strip(),
                        },
                        "doc": doc,
                    }
                )

    texts = []
    for item in chunks:
        content = item["chunk"]["content"]
        title = item["doc"].get("title", "")
        if title:
            content = f"{title}\n\n{content}"
        texts.append(content)
    
    embeddings = await embedding.embed_batch(texts)

    vectors = []
    for item, emb in zip(chunks, embeddings):
        content = item["chunk"]["content"]
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        chunk_id_str = f"{item['doc']['id']}_chunk_{item['chunk']['chunk_index']}"
        vector_id = int(hashlib.md5(chunk_id_str.encode()).hexdigest()[:15], 16)

        payload = _build_payload(item["doc"], item["chunk"], source_type, content_hash)

        sparse_vector = _calculate_sparse_vector(content)

        vectors.append(
            {
                "id": vector_id,
                "vector": emb,
                "sparse_vector": sparse_vector,
                "metadata": payload.model_dump(exclude_none=True),
            }
        )

    return vectors


def _build_payload(doc: Dict[str, Any], chunk: Dict[str, Any], source_type: str, content_hash: str) -> VectorPayload:
    raw_meta = doc.get("metadata", {})

    updated_at = doc.get("updated_at")
    last_modified_at = None
    if updated_at:
        last_modified_at = updated_at.isoformat() if hasattr(updated_at, "isoformat") else str(updated_at)

    return VectorPayload(
        source_document_id=doc.get("id", ""),
        content=chunk["content"],
        chunk_index=chunk["chunk_index"],
        source_type=source_type,
        title=doc.get("title", ""),
        url=doc.get("url"),
        author=doc.get("author"),
        last_modified_at=last_modified_at,
        hash=content_hash,
        version_key=doc.get("version_key"),
        page_id=raw_meta.get("page_id") if source_type == "confluence" else None,
        space_key=raw_meta.get("space_key") if source_type == "confluence" else None,
        issue_key=raw_meta.get("issue_key") if source_type == "jira" else None,
        project_key=raw_meta.get("project_key") if source_type == "jira" else None,
    )
