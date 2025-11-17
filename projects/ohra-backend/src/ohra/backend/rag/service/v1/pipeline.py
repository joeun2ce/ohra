from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import json
import boto3

from ohra.shared_kernel.infra.embedding.interface import EmbeddingInterface
from ohra.shared_kernel.infra.vector_store.interface import VectorStoreInterface

from .prompt import __SYSTEM_PROMPT__, __PROMPT_TEMPLATE__, format_context_docs
from .settings import LangchainRAGAnalyzerConfig
from .schema import RetrievedDocument
from ohra.backend.rag.dtos.request import ChatCompletionRequest
from ohra.backend.rag.dtos.response import ChatCompletionResponse
from ohra.backend.rag import exceptions


@dataclass
class LangchainRAGAnalyzer:
    embedding: EmbeddingInterface = field(repr=False)
    vector_store: VectorStoreInterface = field(repr=False)
    config: LangchainRAGAnalyzerConfig | dict = field(default_factory=LangchainRAGAnalyzerConfig)

    sagemaker_client: Any = field(init=False, repr=False)

    def __post_init__(self):
        if isinstance(self.config, dict):
            self.config = LangchainRAGAnalyzerConfig(**self.config)

        self.sagemaker_client = boto3.client("sagemaker-runtime", region_name=self.config.region)

    async def ainvoke(
        self,
        request: ChatCompletionRequest,
        filter: Optional[Dict[str, Any]] = None,
    ) -> ChatCompletionResponse:
        user_messages = [msg for msg in request.messages if msg.role == "user"]
        query = user_messages[-1].content

        query_vector = await self.embedding.embed_text(query)
        context_docs_raw = await self.vector_store.search(
            query_vector=query_vector, top_k=self.config.top_k, filter=filter
        )

        context_docs = [RetrievedDocument.model_validate(doc) for doc in context_docs_raw]
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
