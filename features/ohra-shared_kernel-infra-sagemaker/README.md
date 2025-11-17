# ohra-shared-kernel-infra-sagemaker

SageMaker infrastructure adapters for LLM and Embedding services.

## Components

- `SageMakerLLMAdapter` - LLM adapter for SageMaker endpoints
- `SageMakerEmbeddingAdapter` - Embedding adapter for SageMaker endpoints
- `SageMakerSettings` - Configuration settings

## Usage

```python
from ohra.shared_kernel.infra.sagemaker import SageMakerLLMAdapter, SageMakerEmbeddingAdapter

# LLM Adapter
llm = SageMakerLLMAdapter(
    endpoint_name="your-llm-endpoint",
    region="us-west-2"
)

# Embedding Adapter
embedding = SageMakerEmbeddingAdapter(
    endpoint_name="your-embedding-endpoint",
    dimension=1024,
    region="us-west-2"
)
```

