from dependency_injector import containers, providers

from ohra.backend.settings import Settings
from ohra.backend.rag.service.v1.pipeline import LangchainRAGAnalyzer
from ohra.backend.rag.retrieval.vector.retriever import VectorRetriever
from ohra.backend.rag.retrieval.keyword.retriever import BM25Retriever
from ohra.backend.rag.retrieval.hybrid.service import HybridSearchService
from ohra.backend.rag.use_case.chat_use_case import ChatCompletionUseCase
from ohra.backend.rag.use_case.feedback_use_case import FeedbackUseCase


class RAGContainer(containers.DeclarativeContainer):
    settings = providers.Resource(Settings)

    embedding = providers.Dependency()
    vector_store = providers.Dependency()

    vector_retriever = providers.Factory(
        VectorRetriever,
        vector_store=vector_store,
        embedding=embedding,
    )

    keyword_retriever = providers.Factory(
        BM25Retriever,
        vector_store=vector_store,
    )

    hybrid_search_service = providers.Factory(
        HybridSearchService,
        vector_retriever=vector_retriever,
        keyword_retriever=keyword_retriever,
        rrf_k=settings.provided.rag_analyzer.rrf_k,
    )

    analyzer = providers.Factory(
        LangchainRAGAnalyzer,
        config=settings.provided.rag_analyzer,
        embedding=embedding,
        vector_store=vector_store,
    )

    chat_completion_use_case = providers.Factory(ChatCompletionUseCase, analyzer=analyzer)

    feedback_use_case = providers.Singleton(FeedbackUseCase)
