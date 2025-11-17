# ohra-shared-kernel-infra-qdrant

Qdrant vector store infrastructure adapter.

## Components

- `QdrantAdapter` - Vector store adapter for Qdrant
- `QdrantSettings` - Configuration settings

## Usage

```python
from ohra.shared_kernel.infra.qdrant import QdrantAdapter

# Create adapter
adapter = QdrantAdapter(
    host="localhost",
    port=6333,
    collection_name="ohra_documents"
)

# Create collection
await adapter.create_collection("ohra_documents", vector_size=768)

# Upsert vector
await adapter.upsert(
    id="doc-1",
    vector=[0.1, 0.2, 0.3, ...],
    metadata={"title": "Document 1", "content": "..."}
)

# Search
results = await adapter.search(
    query_vector=[0.1, 0.2, 0.3, ...],
    top_k=5
)
```

