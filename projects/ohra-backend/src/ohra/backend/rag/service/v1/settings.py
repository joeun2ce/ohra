from pydantic import BaseModel, Field


class LangchainRAGAnalyzerConfig(BaseModel):
    model_name: str = Field(default="Qwen/Qwen3-4B-Instruct-2507")
    endpoint_name: str = Field(default="qwen3-4b-instruct-2507-vllm-endpoint-1")
    region: str = Field(default="ap-northeast-2")
    top_k: int = Field(default=5)
    score_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    stream: bool = Field(default=False)
