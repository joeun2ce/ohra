from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, Field
from ohra.shared_kernel.infra.sagemaker import SageMakerSettings
from ohra.shared_kernel.infra.qdrant import QdrantSettings


class AtlassianSettings(BaseModel):
    email: str
    base_url: str
    token: str

    @property
    def confluence_url(self) -> str:
        return self.base_url.rstrip("/")

    @property
    def jira_url(self) -> str:
        return self.base_url.rstrip("/")


class WorkerSyncSettings(BaseModel):
    sync_interval_hours: int = Field(default=1)
    embedding_batch_size: int = Field(default=5)


class WorkerSettings(BaseSettings):
    db_url: str = "sqlite+aiosqlite:///./projects/ohra-backend/data/database.db"

    atlassian_email: str = ""
    atlassian_base_url: str = ""
    atlassian_token: str = ""

    sagemaker_embedding_endpoint: str = "qwen3-embedding-0-6b-endpoint"
    sagemaker_embedding_dimension: int = 1024
    sagemaker_region: str = "ap-northeast-2"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "ohra_documents"

    worker_sync_interval_hours: int = 1
    worker_embedding_batch_size: int = 5

    @property
    def atlassian(self) -> AtlassianSettings:
        return AtlassianSettings(
            email=self.atlassian_email,
            base_url=self.atlassian_base_url,
            token=self.atlassian_token,
        )

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
    def worker(self) -> WorkerSyncSettings:
        return WorkerSyncSettings(
            sync_interval_hours=self.worker_sync_interval_hours,
            embedding_batch_size=self.worker_embedding_batch_size,
        )

    model_config = SettingsConfigDict(env_prefix="OHRA_", case_sensitive=False, env_file=".env", extra="allow")
