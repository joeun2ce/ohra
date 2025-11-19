from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import json
import boto3

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
        query = next((msg.content for msg in reversed(request.messages) if msg.role == "user"), "")

        print(f"[RAG] Query: {query[:100]}, top_k: {self.config.top_k}, mode: {self.config.search_mode}", flush=True)
        context_docs = await self.hybrid_retriever.retrieve(
            query=query,
            top_k=self.config.top_k,
            filter=filter,
            search_mode=self.config.search_mode,
        )
        print(f"[RAG] Found {len(context_docs)} documents", flush=True)
        if context_docs:
            print(f"[RAG] First doc: {context_docs[0].title[:50]}... (score: {context_docs[0].score:.4f})", flush=True)
        else:
            print("[RAG] No documents found!", flush=True)
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
            response = self.sagemaker_client.invoke_endpoint(
                EndpointName=self.config.endpoint_name, ContentType="application/json", Body=json.dumps(payload)
            )

            result = json.loads(response["Body"].read())

            chat_response = ChatCompletionResponse(**result)
            chat_response.model = request.model or self.config.model_name

            return chat_response
        except Exception as e:
            raise exceptions.RAGException(f"Failed to invoke SageMaker endpoint: {str(e)}")
