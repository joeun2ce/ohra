"""API 클라이언트 헬퍼"""
import os
import aiohttp
import time
from typing import Dict, Any, Optional


BASE_URL = os.getenv("OHRA_API_URL", "http://localhost:8000")


def get_api_key() -> str:
    """API 키를 동적으로 가져오기 (conftest.py에서 설정됨)"""
    api_key = os.getenv("OHRA_API_KEY")
    if not api_key:
        raise ValueError("OHRA_API_KEY environment variable is not set. Make sure conftest.py is loaded.")
    return api_key


async def make_chat_request(
    session: aiohttp.ClientSession,
    query: str,
    conversation_id: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    stream: bool = False,
) -> Dict[str, Any]:
    """채팅 완성 요청"""
    url = f"{BASE_URL}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }
    
    messages = [{"role": "user", "content": query}]
    payload = {
        "model": "Qwen/Qwen3-4B-Instruct-2507",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream,
    }
    
    if conversation_id:
        payload["user"] = conversation_id
    
    start_time = time.time()
    try:
        async with session.post(url, json=payload, headers=headers) as response:
            elapsed = time.time() - start_time
            result = await response.json()
            
            response_text = ""
            if result.get("choices") and len(result["choices"]) > 0:
                response_text = result["choices"][0].get("message", {}).get("content", "")
            
            return {
                "status": response.status,
                "elapsed_time": elapsed,
                "response": result,
                "response_text": response_text,
                "usage": result.get("usage", {}),
            }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "status": 0,
            "elapsed_time": elapsed,
            "error": str(e),
        }


async def make_embedding_request(
    session: aiohttp.ClientSession,
    text: str,
) -> Optional[Dict[str, Any]]:
    """임베딩 요청"""
    url = f"{BASE_URL}/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }
    payload = {"input": text}
    
    try:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                if result.get("data") and len(result["data"]) > 0:
                    return {
                        "status": response.status,
                        "embedding": result["data"][0].get("embedding"),
                    }
    except Exception as e:
        pass
    
    return None

