from dependency_injector import containers, providers

from ohra.backend.settings import Settings
from ohra.backend.rag.service.v1.pipeline import LangchainRAGAnalyzer
from ohra.backend.rag.use_case.chat_use_case import ChatCompletionUseCase
from ohra.backend.rag.use_case.feedback_use_case import FeedbackUseCase


class RAGContainer(containers.DeclarativeContainer):
    settings = providers.Resource(Settings)

    embedding = providers.Dependency()
    vector_store = providers.Dependency()

    analyzer = providers.Factory(
        LangchainRAGAnalyzer,
        config=settings.provided.rag_analyzer,
        embedding=embedding,
        vector_store=vector_store,
    )

    chat_completion_use_case = providers.Factory(ChatCompletionUseCase, analyzer=analyzer)

    feedback_use_case = providers.Singleton(FeedbackUseCase)
