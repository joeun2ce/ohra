from functools import wraps
from typing import Callable, Optional
from datetime import datetime
import gc
from ohra.workers.settings import WorkerSettings
from ohra.shared_kernel.infra.sagemaker import SageMakerEmbeddingAdapter
from ohra.shared_kernel.infra.qdrant import QdrantAdapter
from ohra.workers.sync.utils.transform import transform_batch
from ohra.workers.sync.utils.load import load_batch


def sync_script(
    source_type: str,
    chunk_size: int = 1500,
    chunk_overlap: int = 300,
    get_config: Optional[Callable] = None,
):
    """
    스크립트 데코레이터 - 공통 ETL 파이프라인 처리

    Args:
        source_type: 소스 타입 (예: "confluence", "jira", "notion", "slack", "github")
        chunk_size: 청킹 크기
        chunk_overlap: 청킹 오버랩
        get_config: settings에서 플랫폼별 설정을 가져오는 함수
                    예: lambda s: {"url": s.atlassian.confluence_url,
                                   "email": s.atlassian.email,
                                   "token": s.atlassian.token}
                    또는 lambda s: {"token": s.notion_token, "database_id": s.notion_database_id}

    사용법:
        @sync_script(
            source_type="confluence",
            chunk_size=1500,
            chunk_overlap=300,
            get_config=lambda s: {
                "url": s.atlassian.confluence_url,
                "email": s.atlassian.email,
                "token": s.atlassian.token
            }
        )
        def extract_documents(**config) -> Generator[Dict[str, Any], None, None]:
            # config에서 url, email, token 등 사용
            # 문서를 yield
            yield {
                "id": "...",
                "title": "...",
                "content": "...",
                ...
            }
    """

    def decorator(extract_func: Callable) -> Callable:
        @wraps(extract_func)
        async def async_wrapper(last_sync_time: Optional[datetime] = None):
            print(
                f"[Worker] async_wrapper started - source_type: {source_type}, last_sync_time: {last_sync_time}",
                flush=True,
            )
            settings = WorkerSettings()

            if get_config:
                config = get_config(settings)
                print(f"[Worker] Config loaded for {source_type}", flush=True)
            else:
                config = {}

            print("[Worker] Initializing embedding adapter...", flush=True)
            embedding = SageMakerEmbeddingAdapter(
                endpoint_name=settings.sagemaker.embedding_endpoint,
                dimension=settings.sagemaker.embedding_dimension,
                region=settings.sagemaker.region,
            )

            print("[Worker] Initializing Qdrant adapter...", flush=True)
            vector_store = QdrantAdapter(
                host=settings.qdrant.host, port=settings.qdrant.port, collection_name=settings.qdrant.collection_name
            )

            print("[Worker] Ensuring collection exists...", flush=True)
            await vector_store.ensure_collection_exists(
                vector_size=settings.sagemaker.embedding_dimension, enable_sparse=True
            )
            print("[Worker] Collection ready", flush=True)

            doc_batch = []
            chunk_buffer = []
            documents_synced = 0
            vectors_upserted = 0
            skipped = 0

            print("[Worker] Starting document extraction...", flush=True)
            extract_gen = extract_func(last_sync_time=last_sync_time, **config)
            print("[Worker] Document extractor generator created", flush=True)

            try:
                doc_count = 0
                for doc in extract_gen:
                    doc_count += 1
                    if doc_count % 10 == 0:
                        print(f"[Worker] Processing document {doc_count}...", flush=True)
                    doc_id = doc.get("id", "")
                    version_key = doc.get("version_key")

                    if version_key:
                        existing = await vector_store.get_by_filter(
                            {"source_document_id": doc_id, "source_type": source_type}, limit=1
                        )
                        if existing:
                            existing_version = existing[0].get("metadata", {}).get("version_key")
                            if existing_version == version_key:
                                skipped += 1
                                if skipped % 10 == 0:
                                    print(f"[Worker] Skipped {skipped} documents (unchanged)", flush=True)
                                continue
                            await vector_store.delete_by_filter(
                                {"source_document_id": doc_id, "source_type": source_type}
                            )

                    doc_batch.append(doc)

                    if len(doc_batch) >= 10:
                        vectors = await transform_batch(
                            source_type=source_type,
                            documents=doc_batch,
                            embedding=embedding,
                            chunk_size=chunk_size,
                            chunk_overlap=chunk_overlap,
                        )
                        chunk_buffer.extend(vectors)
                        doc_batch.clear()
                        documents_synced += 10

                    if len(chunk_buffer) >= 5:
                        loaded = await load_batch(vectors=chunk_buffer[:5], vector_store=vector_store)
                        vectors_upserted += loaded
                        chunk_buffer = chunk_buffer[5:]
                        gc.collect()

                if doc_batch:
                    vectors = await transform_batch(
                        source_type=source_type,
                        documents=doc_batch,
                        embedding=embedding,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                    )
                    chunk_buffer.extend(vectors)
                    documents_synced += len(doc_batch)
                    doc_batch.clear()

                if chunk_buffer:
                    loaded = await load_batch(chunk_buffer, vector_store)
                    vectors_upserted += loaded
                    chunk_buffer.clear()

                print(f"[Worker] Document extraction completed - total: {doc_count}", flush=True)
            except Exception as e:
                print(f"[Worker] ERROR in async_wrapper: {e}", flush=True)
                import traceback

                traceback.print_exc()
                raise
            finally:
                doc_batch.clear()
                chunk_buffer.clear()
                gc.collect()

            print(
                f"[Worker] async_wrapper completed - synced: {documents_synced}, skipped: {skipped}, vectors: {vectors_upserted}",
                flush=True,
            )
            return documents_synced, skipped, vectors_upserted

        return async_wrapper

    return decorator
