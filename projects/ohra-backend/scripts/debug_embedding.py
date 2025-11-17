import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ohra.shared_kernel.infra.sagemaker import SageMakerEmbeddingAdapter
from ohra.shared_kernel.infra.qdrant import QdrantAdapter
from ohra.backend.settings import Settings


async def test_embedding():
    settings = Settings()
    embedding = SageMakerEmbeddingAdapter(
        endpoint_name=settings.sagemaker.embedding_endpoint,
        dimension=settings.sagemaker.embedding_dimension,
        region=settings.sagemaker.region,
    )

    test_text = "아하앤컴퍼니에서 하는 일"
    print(f"Testing embedding for: '{test_text}'")
    try:
        vector = await embedding.embed_text(test_text)
        print(f"✓ Embedding successful: dimension={len(vector)}, first 5 values={vector[:5]}")
        return vector
    except Exception as e:
        print(f"✗ Embedding failed: {e}")
        return None


async def test_vector_store():
    settings = Settings()
    vector_store = QdrantAdapter(
        host=settings.qdrant.host,
        port=settings.qdrant.port,
        collection_name=settings.qdrant.collection_name,
    )

    await vector_store.ensure_collection_exists(vector_size=settings.sagemaker.embedding_dimension)

    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(host=settings.qdrant.host, port=settings.qdrant.port)
        collection_info = client.get_collection(settings.qdrant.collection_name)
        print(f"✓ Collection '{settings.qdrant.collection_name}' exists")
        print(f"  - Points count: {collection_info.points_count}")
        print(f"  - Vector size: {collection_info.config.params.vectors.size}")

        if collection_info.points_count > 0:
            result = client.scroll(
                collection_name=settings.qdrant.collection_name,
                limit=5,
                with_payload=True,
                with_vectors=False,
            )
            points, _ = result
            print(f"\n  Sample documents (first 5):")
            for i, point in enumerate(points, 1):
                payload = point.payload
                print(f"    {i}. ID: {point.id}")
                print(f"       Title: {payload.get('title', 'N/A')}")
                print(f"       Source: {payload.get('source_type', 'N/A')}")
                print(f"       Content preview: {payload.get('content', '')[:100]}...")
                print()
        else:
            print("  ⚠ No documents found in collection!")

        return collection_info.points_count
    except Exception as e:
        print(f"✗ Vector store check failed: {e}")
        return 0


async def test_search():
    settings = Settings()
    embedding = SageMakerEmbeddingAdapter(
        endpoint_name=settings.sagemaker.embedding_endpoint,
        dimension=settings.sagemaker.embedding_dimension,
        region=settings.sagemaker.region,
    )
    vector_store = QdrantAdapter(
        host=settings.qdrant.host,
        port=settings.qdrant.port,
        collection_name=settings.qdrant.collection_name,
    )

    test_queries = [
        "아하앤컴퍼니에서 하는 일",
        "AI 아메바가 무슨 일을 하는지",
        "우리 무슨 얘기하고 있어",
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Search query: '{query}'")
        print(f"{'='*60}")

        try:
            query_vector = await embedding.embed_text(query)
            results = await vector_store.search(query_vector=query_vector, top_k=5)

            if results:
                print(f"✓ Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"\n  {i}. Score: {result['score']:.4f}")
                    print(f"     Title: {result['metadata'].get('title', 'N/A')}")
                    print(f"     Source: {result['metadata'].get('source_type', 'N/A')}")
                    content = result['metadata'].get('content', '')
                    print(f"     Content: {content[:150]}..." if len(content) > 150 else f"     Content: {content}")
            else:
                print("  ⚠ No results found!")
        except Exception as e:
            print(f"✗ Search failed: {e}")


async def main():
    print("=" * 60)
    print("Embedding & Vector Store Debug Tool")
    print("=" * 60)

    print("\n[1] Testing Embedding Model...")
    vector = await test_embedding()

    print("\n[2] Checking Vector Store...")
    doc_count = await test_vector_store()

    if doc_count > 0:
        print("\n[3] Testing Search...")
        await test_search()
    else:
        print("\n⚠ Skipping search test - no documents in collection")

    print("\n" + "=" * 60)
    print("Debug complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

