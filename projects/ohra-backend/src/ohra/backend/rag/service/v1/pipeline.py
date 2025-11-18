from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import json
import boto3
import time

from ohra.shared_kernel.infra.sagemaker import SageMakerEmbeddingAdapter
from ohra.shared_kernel.infra.qdrant import QdrantAdapter

from .prompt import __SYSTEM_PROMPT__, __PROMPT_TEMPLATE__, format_context_docs
from .settings import LangchainRAGAnalyzerConfig
from ohra.backend.rag.retrieval.hybrid.retriever import HybridRetriever
from ohra.backend.rag.dtos.request import ChatCompletionRequest
from ohra.backend.rag.dtos.response import ChatCompletionResponse
from ohra.backend.rag import exceptions


@dataclass
class LangchainRAGAnalyzer:
    embedding: SageMakerEmbeddingAdapter = field(repr=False)
    vector_store: QdrantAdapter = field(repr=False)
    config: LangchainRAGAnalyzerConfig | dict = field(default_factory=LangchainRAGAnalyzerConfig)

    sagemaker_client: Any = field(init=False, repr=False)
    hybrid_retriever: HybridRetriever = field(init=False, repr=False)

    def __post_init__(self):
        if isinstance(self.config, dict):
            self.config = LangchainRAGAnalyzerConfig(**self.config)

        self.sagemaker_client = boto3.client("sagemaker-runtime", region_name=self.config.region)

        self.hybrid_retriever = HybridRetriever(
            vector_store=self.vector_store,
            embedding=self.embedding,
        )

    async def ainvoke(
        self,
        request: ChatCompletionRequest,
        filter: Optional[Dict[str, Any]] = None,
    ) -> ChatCompletionResponse:
        total_start = time.time()
        query = next((msg.content for msg in reversed(request.messages) if msg.role == "user"), "")

        search_start = time.time()
        context_docs = await self.hybrid_retriever.retrieve(
            query=query,
            top_k=self.config.top_k,
            filter=filter,
            search_mode=self.config.search_mode,
        )
        search_time = time.time() - search_start
        context_text = format_context_docs(context_docs)

        enhanced_query = __PROMPT_TEMPLATE__.format(context=context_text, question=query)

        messages = [
            {"role": "system", "content": __SYSTEM_PROMPT__},
            *[{"role": msg.role, "content": msg.content} for msg in request.messages[-5:-1]],
            {"role": "user", "content": enhanced_query},
        ]

        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": self.config.stream,
        }

        try:
            llm_start = time.time()
            response = self.sagemaker_client.invoke_endpoint(
                EndpointName=self.config.endpoint_name, ContentType="application/json", Body=json.dumps(payload)
            )

            result = json.loads(response["Body"].read())
            llm_time = time.time() - llm_start
            total_time = time.time() - total_start

            chat_response = ChatCompletionResponse(**result)
            chat_response.model = request.model or self.config.model_name

            # Performance log for report
            print("\n" + "=" * 80)
            print("RAG PIPELINE PERFORMANCE METRICS")
            print("=" * 80)
            print(f"Query: {query[:60]}...")
            print(f"Search Mode: {self.config.search_mode}")
            print(f"Retrieved Documents: {len(context_docs)}")
            print(f"Search Time: {search_time:.3f}s")
            print(f"LLM Inference Time: {llm_time:.3f}s")
            print(f"Total Response Time: {total_time:.3f}s")
            if result.get("usage"):
                print(f"Tokens - Prompt: {result['usage'].get('prompt_tokens', 'N/A')}, "
                      f"Completion: {result['usage'].get('completion_tokens', 'N/A')}, "
                      f"Total: {result['usage'].get('total_tokens', 'N/A')}")
            print("=" * 80 + "\n")

            return chat_response
        except Exception as e:
            raise exceptions.RAGException(f"Failed to invoke SageMaker endpoint: {str(e)}")
