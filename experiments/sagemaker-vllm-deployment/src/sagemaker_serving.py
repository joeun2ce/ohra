import asyncio
import os
import sys
import logging
import uvicorn
from typing import Optional
from pydantic import ValidationError
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.entrypoints.openai.serving_chat import OpenAIServingChat
from vllm.entrypoints.openai.protocol import ChatCompletionRequest, ChatCompletionResponse, ErrorResponse

# 레퍼런스 코드에 맞게 import 수정
from vllm.entrypoints.openai.serving_models import BaseModelPath, OpenAIServingModels

# Logger 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

instance_to_gpus = {
    "ml.g5.4xlarge": 1,  # A10G （24 GB）
    "ml.g6.4xlarge": 1,  # L4 （24 GB）
    "ml.g5.12xlarge": 4,  # A10G （24 GB * 4）
    "ml.g6.12xlarge": 4,  # L4（24 GB * 4）
    "ml.g5.48xlarge": 8,  # A10G（24 GB * 8）
    "ml.g6.48xlarge": 8,  # L4 （24 GB * 4）
    "ml.p4d.24xlarge": 8,  # A100 （40 GB * 8）
    "ml.p4de.24xlarge": 8,  # A100 （80 GB * 8）
    "ml.p5.48xlarge": 8,  # H100 （80 GB * 8）
}


def get_num_gpus(instance_type):
    try:
        return instance_to_gpus[instance_type]
    except KeyError:
        raise ValueError(f"Instance type {instance_type} not found in the dictionary")


app = FastAPI()

# Global variables
engine: Optional[AsyncLLMEngine] = None
openai_serving_chat: Optional[OpenAIServingChat] = None


# As sagemaker endpoint requires...
@app.get("/ping")
def ping():
    return JSONResponse(content={}, status_code=status.HTTP_200_OK)


# As sagemaker endpoint requires...
@app.post("/invocations")
async def invocations(request: Request):
    global openai_serving_chat

    if openai_serving_chat is None:
        return JSONResponse(content={"error": "Model not loaded"}, status_code=503)

    try:
        payload = await request.json()
        chat_completion_request = ChatCompletionRequest(**payload)
    except ValidationError as e:
        return JSONResponse(content={"error": "Invalid request format", "details": e.errors()}, status_code=400)

    generator = await openai_serving_chat.create_chat_completion(chat_completion_request, request)

    if isinstance(generator, ErrorResponse):
        error_dict = generator.model_dump()
        status_code = getattr(generator, "code", 400)
        return JSONResponse(content=error_dict, status_code=status_code)

    if "stream" in payload and payload.get("stream"):
        return StreamingResponse(content=generator, media_type="text/event-stream")
    else:
        assert isinstance(generator, ChatCompletionResponse)
        return JSONResponse(content=generator.model_dump())


def start_api_server():
    global engine, openai_serving_chat

    # Get configuration from environment variables
    model_id = os.getenv("MODEL_ID")
    if model_id is None:
        sys.exit("MODEL_ID must be provided")

    instance_type = os.getenv("INSTANCE_TYPE")
    if instance_type is None:
        sys.exit("INSTANCE_TYPE environment variable must be provided")

    try:
        tensor_parallel_size = get_num_gpus(instance_type)
    except ValueError as e:
        sys.exit(f"Invalid INSTANCE_TYPE: {e}")

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8080))
    uvicorn_log_level = os.getenv("UVICORN_LOG_LEVEL", "info")

    logger.info("Starting SageMaker vLLM server")
    logger.info(f"  Model: {model_id}")
    logger.info(f"  Instance Type: {instance_type}")
    logger.info(f"  Tensor Parallel Size: {tensor_parallel_size}")

    # Create engine args manually
    engine_args = AsyncEngineArgs(
        model=model_id,
        tensor_parallel_size=tensor_parallel_size,
        trust_remote_code=True,
        dtype="bfloat16",
        max_model_len=16384,  # RAG를 위해 16384로 증가
        gpu_memory_utilization=0.45,
        enforce_eager=True,  # Disable CUDA graph for stability
    )

    # Initialize engine
    engine = AsyncLLMEngine.from_engine_args(engine_args)

    # Get model config
    event_loop: Optional[asyncio.AbstractEventLoop]
    try:
        event_loop = asyncio.get_running_loop()
    except RuntimeError:
        event_loop = None

    if event_loop is not None and event_loop.is_running():
        model_config = event_loop.run_until_complete(engine.get_model_config())
    else:
        model_config = asyncio.run(engine.get_model_config())

    # AsyncLLMEngine은 EngineClient를 구현합니다
    engine_client = engine

    # OpenAIServingModels 생성 - 레퍼런스 코드 방식 사용
    base_model_paths = [BaseModelPath(name=model_id, model_path=model_id)]

    openai_serving_models = OpenAIServingModels(
        engine_client=engine_client,
        model_config=model_config,
        base_model_paths=base_model_paths,
    )

    # Initialize OpenAI serving chat
    openai_serving_chat = OpenAIServingChat(
        engine_client=engine_client,
        model_config=model_config,
        models=openai_serving_models,
        response_role="assistant",
        request_logger=None,
        chat_template=None,
        chat_template_content_format="auto",
    )

    logger.info("Model loaded successfully. Starting server...")

    # Spin up the API server
    uvicorn.run(app, host=host, port=port, log_level=uvicorn_log_level)


if __name__ == "__main__":
    start_api_server()
