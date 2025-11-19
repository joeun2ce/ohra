from pydantic import BaseModel, Field


class LangchainRAGAnalyzerConfig(BaseModel):
    model_name: str = Field(default="Qwen/Qwen3-4B-Instruct-2507")
    endpoint_name: str = Field(default="qwen3-4b-instruct-2507-vllm-endpoint-1")
    region: str = Field(default="ap-northeast-2")
    top_k: int = Field(default=5)
    stream: bool = Field(default=False)
    rrf_k: int = Field(default=60)  # RRF constant default 60
