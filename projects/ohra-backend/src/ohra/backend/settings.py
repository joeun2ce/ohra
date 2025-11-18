from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from ohra.shared_kernel.domain.enum import ApplicationMode
from ohra.shared_kernel.infra.settings.model import (
    SessionSettings,
    CORSSettings,
    FastAPISettings,
    GZipSettings,
)
from ohra.shared_kernel.infra.database.sqla.settings import DatabaseSettings
from ohra.shared_kernel.infra.sagemaker import SageMakerSettings
from ohra.shared_kernel.infra.qdrant import QdrantSettings
from ohra.backend.rag.service.v1.settings import LangchainRAGAnalyzerConfig


class Settings(BaseSettings):
    mode: ApplicationMode = ApplicationMode.devel

    db_url: str = "sqlite+aiosqlite:///./projects/ohra-backend/data/database.db"

    sagemaker_llm_endpoint: str = "qwen3-4b-instruct-2507-vllm-endpoint-1"
    sagemaker_embedding_endpoint: str = "qwen3-embedding-0-6b-endpoint"
    sagemaker_embedding_dimension: int = 1024
    sagemaker_region: str = "ap-northeast-2"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "ohra_documents"

    cors: CORSSettings = Field(default_factory=CORSSettings)
    gzip: GZipSettings = Field(default_factory=GZipSettings)
    fastapi: FastAPISettings = Field(
        default_factory=lambda: FastAPISettings(
            title="ohra API",
            description="ohra API",
            docs_url="/docs/openapi",
            openapi_url="/v1/openapi.json",
            redoc_url="/redoc",
        )
    )
    session: SessionSettings = Field(default_factory=SessionSettings)

    @property
    def db(self) -> DatabaseSettings:
        return DatabaseSettings(url=self.db_url)

    @property
    def sagemaker(self) -> SageMakerSettings:
        return SageMakerSettings(
            embedding_endpoint=self.sagemaker_embedding_endpoint,
            embedding_dimension=self.sagemaker_embedding_dimension,
            region=self.sagemaker_region,
        )

    @property
    def qdrant(self) -> QdrantSettings:
        return QdrantSettings(
            host=self.qdrant_host,
            port=self.qdrant_port,
            collection_name=self.qdrant_collection_name,
        )

    @property
    def rag_analyzer(self) -> LangchainRAGAnalyzerConfig:
        return LangchainRAGAnalyzerConfig(
            endpoint_name=self.sagemaker_llm_endpoint,
            region=self.sagemaker_region,
        )

    model_config = SettingsConfigDict(env_prefix="OHRA_", env_file=".env", env_file_encoding="utf-8", extra="allow")


Settings.model_rebuild()
