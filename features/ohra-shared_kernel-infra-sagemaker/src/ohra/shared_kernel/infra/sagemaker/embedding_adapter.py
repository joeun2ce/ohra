import logging
import boto3
import json
from typing import List, Optional
from ohra.shared_kernel.infra.embedding.exceptions import EmbeddingException

logger = logging.getLogger(__name__)


class SageMakerEmbeddingAdapter:
    def __init__(self, endpoint_name: str, dimension: int, region: str = "us-west-2"):
        self.client = boto3.client("sagemaker-runtime", region_name=region)
        self.endpoint_name = endpoint_name
        self._expected_dimension = dimension
        self._actual_dimension: Optional[int] = None
        self.region = region

    @property
    def dimension(self) -> int:
        return self._actual_dimension if self._actual_dimension else self._expected_dimension

    async def embed_text(self, text: str) -> List[float]:
        payload = {"inputs": [text]}

        try:
            response = self.client.invoke_endpoint(
                EndpointName=self.endpoint_name, ContentType="application/json", Body=json.dumps(payload)
            )

            result = json.loads(response["Body"].read())

            if "data" in result:
                # inference.py format: {"data": [{"embedding": [...]}, ...]}
                embedding = result["data"][0]["embedding"]
            elif "embeddings" in result:
                embedding = result["embeddings"][0]
            else:
                raise EmbeddingException(f"Unexpected response format: {result.keys()}")

            actual_dim = len(embedding)
            self._update_dimension(actual_dim)

            return embedding
        except Exception as e:
            raise EmbeddingException(f"Failed to embed text: {e}") from e

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        batch_size = 32  # Limit batch size
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            payload = {"inputs": batch}

            try:
                response = self.client.invoke_endpoint(
                    EndpointName=self.endpoint_name, ContentType="application/json", Body=json.dumps(payload)
                )

                result = json.loads(response["Body"].read())

                if "data" in result:
                    embeddings = [item["embedding"] for item in result["data"]]
                elif "embeddings" in result:
                    embeddings = result["embeddings"]
                else:
                    raise EmbeddingException(f"Unexpected response format: {result.keys()}")

                for emb in embeddings:
                    actual_dim = len(emb)
                    self._update_dimension(actual_dim)

                all_embeddings.extend(embeddings)
            except Exception as e:
                raise EmbeddingException(f"Failed to embed batch: {e}") from e

        return all_embeddings

    def _update_dimension(self, actual_dim: int) -> None:
        if self._actual_dimension is None:
            self._actual_dimension = actual_dim
            if actual_dim != self._expected_dimension:
                logger.warning(
                    f"Embedding dimension mismatch: expected {self._expected_dimension}, "
                    f"got {actual_dim}. Using actual dimension {actual_dim}."
                )
        elif self._actual_dimension != actual_dim:
            logger.error(f"Inconsistent embedding dimensions: previously {self._actual_dimension}, now {actual_dim}")
