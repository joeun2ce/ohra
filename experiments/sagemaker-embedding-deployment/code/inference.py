from djl_python import Input, Output
import logging
import os
import glob
from llama_cpp import Llama

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

model = None


def find_gguf_file(model_dir: str) -> str:
    """Find first available GGUF file."""
    for pattern in ["*.gguf", "**/*.gguf"]:
        matches = glob.glob(os.path.join(model_dir, pattern), recursive=True)
        if matches:
            return matches[0]
    raise FileNotFoundError(f"No GGUF file found in {model_dir}")


def load_model(properties):
    """Load Qwen3-embedding GGUF model using Llama.from_pretrained()."""
    global model

    model_id = properties.get("model_id")
    if not model_id:
        raise ValueError("model_id must be set in serving.properties")

    # Parse model_id and filename
    # Format: REPO_ID or REPO_ID:FILENAME
    parts = model_id.split(":", 1)
    repo_id = parts[0]
    filename = parts[1] if len(parts) > 1 else None

    # If filename not specified, try to get from properties or use default pattern
    if not filename:
        filename = properties.get("filename")
        if not filename:
            # Auto-detect: try Q8_0 first, then others
            from huggingface_hub import list_repo_files

            try:
                files = [f for f in list_repo_files(repo_id) if f.endswith(".gguf")]
                for pref in ["Q8_0", "Q4_K_M", "Q4_0"]:
                    for f in files:
                        if pref.lower() in f.lower():
                            filename = f
                            break
                    if filename:
                        break
                if not filename and files:
                    filename = files[0]
            except Exception as e:
                logger.warning(f"Could not auto-detect filename: {e}")
                # Fallback to default naming pattern
                filename = "Qwen3-Embedding-0.6B-Q8_0.gguf"

    logger.info(f"Loading model from HuggingFace: {repo_id}, filename: {filename}")

    n_ctx = int(properties.get("n_ctx", 1024))
    n_threads = int(properties.get("n_threads", 4))
    n_gpu_layers = (
        -1 if str(properties.get("n_gpu_layers", "-1")) in ("-1", "auto") else int(properties.get("n_gpu_layers", "-1"))
    )

    # Use Llama.from_pretrained() to download and load model
    # embedding=True is required for embedding models
    model = Llama.from_pretrained(
        repo_id=repo_id,
        filename=filename,
        embedding=True,  # Add this parameter for embedding models
        n_ctx=n_ctx,
        n_threads=n_threads,
        n_gpu_layers=n_gpu_layers,
        verbose=False,
    )
    logger.info("Model loaded successfully")
    return model


def handle(inputs: Input):
    """Handle inference requests."""
    global model

    if model is None:
        model = load_model(inputs.get_properties())

    if inputs.is_empty():
        return None

    data = inputs.get_as_json()
    properties = inputs.get_properties()

    texts = data.get("input") or data.get("prompt") or data.get("inputs")
    if not texts:
        return Output().error("Input text is required")

    if isinstance(texts, str):
        texts = [texts]

    max_length = int(data.get("max_length", properties.get("max_length", 1024)))
    embeddings = []

    for text in texts:
        if len(text) > max_length * 4:
            text = text[: max_length * 4]
        embeddings.append(model.embed(text))

    result = {
        "object": "list",
        "data": [{"object": "embedding", "index": i, "embedding": emb} for i, emb in enumerate(embeddings)],
        "model": "qwen3-embedding-0.6b-gguf",
        "usage": {
            "prompt_tokens": sum(len(t.split()) for t in texts),
            "total_tokens": sum(len(t.split()) for t in texts),
        },
    }

    output = Output()
    output.add_as_json(result)
    return output
