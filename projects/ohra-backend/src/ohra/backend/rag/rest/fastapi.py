from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Body, status

from ohra.backend.container import OhraContainer
from ohra.backend.rag.use_case.chat_use_case import ChatCompletionUseCase
from ohra.backend.rag.use_case.feedback_use_case import FeedbackUseCase
from ohra.backend.rag.dtos.request import (
    ChatCompletionRequest,
    EmbeddingRequest,
    FeedbackRequest,
)
from ohra.backend.rag.dtos.response import (
    ChatCompletionResponse,
    EmbeddingResponse,
    EmbeddingData,
    ModelsResponse,
)
from ohra.backend.rag.dtos.schemas import ModelInfo
from ohra.backend.auth.dependencies import get_current_user_id
from ohra.shared_kernel.infra.sagemaker import SageMakerEmbeddingAdapter
from ohra.backend.rag import exceptions

router = APIRouter(prefix="/v1", tags=["rag"])

get_chat_use_case = Provide[OhraContainer.rag.chat_completion_use_case]
get_feedback_use_case = Provide[OhraContainer.rag.feedback_use_case]
get_embedding = Provide[OhraContainer.embedding]


@router.get("/models", response_model=ModelsResponse)
async def list_models() -> ModelsResponse:
    return ModelsResponse(
        object="list",
        data=[
            ModelInfo(id="Qwen/Qwen3-4B-Instruct-2507"),
            ModelInfo(id="ohra-embedding"),
        ],
    )


@router.post("/chat/completions", response_model=ChatCompletionResponse)
@inject
async def chat_completion(
    *,
    use_case: ChatCompletionUseCase = Depends(get_chat_use_case),
    user_id: str = Depends(get_current_user_id),
    payload: ChatCompletionRequest = Body(),
) -> ChatCompletionResponse:
    return await use_case.execute(user_id=user_id, request=payload)


@router.post("/feedback", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def submit_feedback(
    *,
    use_case: FeedbackUseCase = Depends(get_feedback_use_case),
    user_id: str = Depends(get_current_user_id),
    payload: FeedbackRequest = Body(),
):
    await use_case.execute(
        user_id=user_id,
        message_id=payload.message_id,
        rating=payload.rating,
        comment=payload.comment,
    )


@router.post("/embeddings", response_model=EmbeddingResponse)
@inject
async def create_embedding(
    *,
    embedding: SageMakerEmbeddingAdapter = Depends(get_embedding),
    payload: EmbeddingRequest = Body(),
) -> EmbeddingResponse:
    if isinstance(payload.input, str):
        if not payload.input.strip():
            raise exceptions.EmbeddingException("Input text cannot be empty")
        embeddings = [await embedding.embed_text(payload.input)]
    else:
        if not payload.input:
            raise exceptions.EmbeddingException("Input list cannot be empty")
        embeddings = await embedding.embed_batch(payload.input)

    return EmbeddingResponse(
        data=[EmbeddingData(embedding=emb, index=i) for i, emb in enumerate(embeddings)],
        model=payload.model,
        usage={"prompt_tokens": 0, "total_tokens": 0},
    )
