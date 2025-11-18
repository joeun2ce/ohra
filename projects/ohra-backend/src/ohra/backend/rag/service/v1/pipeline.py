from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import json
import boto3

from ohra.shared_kernel.infra.sagemaker import SageMakerEmbeddingAdapter
from ohra.shared_kernel.infra.qdrant import QdrantAdapter

from .prompt import __SYSTEM_PROMPT__, __PROMPT_TEMPLATE__, format_context_docs
from .settings import LangchainRAGAnalyzerConfig
from .schema import RetrievedDocument
from ohra.backend.rag.retrieval.vector.retriever import VectorRetriever
from ohra.backend.rag.retrieval.keyword.retriever import BM25Retriever
from ohra.backend.rag.retrieval.hybrid.service import HybridSearchService
from ohra.backend.rag.dtos.request import ChatCompletionRequest
from ohra.backend.rag.dtos.response import ChatCompletionResponse
from ohra.backend.rag import exceptions


@dataclass
class LangchainRAGAnalyzer:
    embedding: SageMakerEmbeddingAdapter = field(repr=False)
    vector_store: QdrantAdapter = field(repr=False)
    config: LangchainRAGAnalyzerConfig | dict = field(default_factory=LangchainRAGAnalyzerConfig)

    sagemaker_client: Any = field(init=False, repr=False)
    hybrid_search_service: Optional[HybridSearchService] = field(init=False, repr=False, default=None)

    def __post_init__(self):
        if isinstance(self.config, dict):
            self.config = LangchainRAGAnalyzerConfig(**self.config)

        self.sagemaker_client = boto3.client("sagemaker-runtime", region_name=self.config.region)

        vector_retriever = VectorRetriever(vector_store=self.vector_store, embedding=self.embedding)
        keyword_retriever = BM25Retriever(vector_store=self.vector_store)
        self.hybrid_search_service = HybridSearchService(
            vector_retriever=vector_retriever,
            keyword_retriever=keyword_retriever,
            rrf_k=self.config.rrf_k,
        )

    async def ainvoke(
        self,
        request: ChatCompletionRequest,
        filter: Optional[Dict[str, Any]] = None,
    ) -> ChatCompletionResponse:
        user_messages = [msg for msg in request.messages if msg.role == "user"]
        query = user_messages[-1].content

        # Use hybrid search service
        context_docs = await self.hybrid_search_service.search(
            query=query,
            top_k=self.config.top_k,
            filter=filter,
            search_mode=self.config.search_mode,
        )
        context_text = format_context_docs(context_docs)

        # 이전 대화 내역 포함 (최근 5개 메시지: user+assistant 쌍 약 2-3개)
        # 문맥 유지를 위해 최근 대화만 포함하여 토큰 수 제한
        history_messages = [{"role": msg.role, "content": msg.content} for msg in request.messages[:-1]][-5:]

        query = user_messages[-1].content
        enhanced_query = __PROMPT_TEMPLATE__.format(context=context_text, question=query)

        messages = [
            {"role": "system", "content": __SYSTEM_PROMPT__},
            *history_messages,
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
