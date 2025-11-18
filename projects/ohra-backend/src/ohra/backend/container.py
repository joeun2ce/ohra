from dependency_injector import containers, providers

from ohra.backend.settings import Settings
from ohra.backend.auth.containers.di import AuthContainer
from ohra.backend.rag.containers.di import RAGContainer
from ohra.shared_kernel.infra.database.sqla.container.di import SqlaContainer
from ohra.shared_kernel.infra.sagemaker import SageMakerEmbeddingAdapter
from ohra.shared_kernel.infra.qdrant import QdrantAdapter


class OhraContainer(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        packages=[],
        modules=[
            "ohra.shared_kernel.infra.database.sqla.mixin",
            "ohra.backend.auth.rest.fastapi",
            "ohra.backend.rag.rest.fastapi",
            "ohra.backend.rag.service.v1.pipeline",
        ],
    )

    settings = providers.Resource(Settings)  # type: ignore
    database = providers.Container(SqlaContainer, settings=settings.provided.db)

    embedding = providers.Singleton(
        SageMakerEmbeddingAdapter,
        endpoint_name=settings.provided.sagemaker.embedding_endpoint,
        dimension=settings.provided.sagemaker.embedding_dimension,
        region=settings.provided.sagemaker.region,
    )

    vector_store = providers.Singleton(
        QdrantAdapter,
        host=settings.provided.qdrant.host,
        port=settings.provided.qdrant.port,
        collection_name=settings.provided.qdrant.collection_name,
    )

    auth = providers.Container(AuthContainer, settings=settings)
    rag = providers.Container(RAGContainer, settings=settings, embedding=embedding, vector_store=vector_store)
