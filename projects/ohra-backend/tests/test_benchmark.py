"""성능 벤치마크 테스트 - 임베딩 품질 및 유사도 검사 포함"""

import pytest
import asyncio
import aiohttp
import time
import numpy as np
import os
from typing import List, Dict, Any, Optional
from tests.utils.test_helpers import save_test_results, generate_markdown_report


BASE_URL = os.getenv("OHRA_API_URL", "http://localhost:8000")
API_KEY = os.getenv("OHRA_API_KEY", "your-api-key-here")  # 환경변수 OHRA_API_KEY에서 가져오기

QUERY_SET = [
    "ai 아메바는 무슨일을 해",
    "어뷰징 경고 알림톡 수신자 필터 기능",
    "배포 프로세스는 어떻게 되나요",
    "Confluence 문서에서 API 명세를 찾아줘",
    "Jira 이슈에서 최근 결정 사항을 알려줘",
]


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """코사인 유사도 계산"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot_product / (norm1 * norm2))


async def get_embedding(session: aiohttp.ClientSession, text: str) -> Optional[List[float]]:
    """텍스트의 임베딩 벡터 가져오기"""
    try:
        # 임베딩 API가 있다면 사용, 없으면 None 반환
        url = f"{BASE_URL}/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {"input": text}

        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                if result.get("data") and len(result["data"]) > 0:
                    return result["data"][0].get("embedding")
    except Exception as e:
        print(f"Warning: Could not get embedding for text: {e}")
    return None


async def make_request(session: aiohttp.ClientSession, query: str) -> Dict[str, Any]:
    """채팅 완성 요청 및 성능 측정"""
    url = f"{BASE_URL}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "Qwen/Qwen3-4B-Instruct-2507",
        "messages": [{"role": "user", "content": query}],
        "temperature": 0.7,
        "max_tokens": 2000,
    }

    start_time = time.time()
    async with session.post(url, json=payload, headers=headers) as response:
        elapsed = time.time() - start_time
        result = await response.json()

        # 응답에서 메시지 추출
        response_text = ""
        if result.get("choices") and len(result["choices"]) > 0:
            response_text = result["choices"][0].get("message", {}).get("content", "")

        return {
            "query": query,
            "status": response.status,
            "elapsed_time": elapsed,
            "response": result,
            "response_text": response_text,
        }


async def analyze_query_quality(session: aiohttp.ClientSession, query: str, response_text: str) -> Dict[str, Any]:
    """쿼리와 응답의 임베딩 유사도 분석"""
    query_embedding = await get_embedding(session, query)
    response_embedding = await get_embedding(session, response_text)

    similarity = None
    if query_embedding and response_embedding:
        similarity = cosine_similarity(query_embedding, response_embedding)

    return {
        "query_embedding_available": query_embedding is not None,
        "response_embedding_available": response_embedding is not None,
        "similarity": similarity,
    }


async def process_query(session: aiohttp.ClientSession, query: str, enable_embedding: bool = True) -> Dict[str, Any]:
    """단일 쿼리 처리 (병렬 처리용)"""
    print(f"[TESTING] Query: {query}")

    # 채팅 완성 요청
    result = await make_request(session, query)

    # 임베딩 품질 분석 (기본 활성화, 실패해도 계속 진행)
    if enable_embedding and result.get("response_text") and result.get("status") == 200:
        try:
            quality = await analyze_query_quality(session, query, result["response_text"])
            result["embedding_quality"] = quality
        except Exception as e:
            print(f"Warning: Embedding analysis failed for query '{query}': {e}")
            result["embedding_quality"] = {
                "query_embedding_available": False,
                "response_embedding_available": False,
                "similarity": None,
                "error": str(e),
            }

    return result


@pytest.mark.asyncio
async def test_benchmark_performance():
    """성능 벤치마크 테스트 - 병렬 처리로 빠른 실행"""
    if API_KEY == "your-api-key-here":
        pytest.skip("API 키가 설정되지 않았습니다. 환경변수 OHRA_API_KEY를 설정하거나 실제 API 키로 교체해주세요.")

    # 임베딩 검사는 시간이 오래 걸리지만 보고서 작성을 위해 기본 활성화
    # 환경변수 OHRA_DISABLE_EMBEDDING=true로 비활성화 가능
    enable_embedding = os.getenv("OHRA_DISABLE_EMBEDDING", "false").lower() != "true"

    results = {
        "test_name": "Performance Benchmark with Embedding Quality",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "queries": [],
        "summary": {},
    }

    async with aiohttp.ClientSession() as session:
        # 병렬 처리로 모든 쿼리를 동시에 실행
        tasks = [process_query(session, query, enable_embedding) for query in QUERY_SET]
        results["queries"] = await asyncio.gather(*tasks)

    # Summary 계산
    elapsed_times = [q["elapsed_time"] for q in results["queries"]]
    similarities = [
        q.get("embedding_quality", {}).get("similarity")
        for q in results["queries"]
        if q.get("embedding_quality", {}).get("similarity") is not None
    ]

    results["summary"] = {
        "total_queries": len(QUERY_SET),
        "avg_response_time": sum(elapsed_times) / len(elapsed_times) if elapsed_times else 0,
        "min_response_time": min(elapsed_times) if elapsed_times else 0,
        "max_response_time": max(elapsed_times) if elapsed_times else 0,
        "avg_similarity": sum(similarities) / len(similarities) if similarities else None,
        "min_similarity": min(similarities) if similarities else None,
        "max_similarity": max(similarities) if similarities else None,
    }

    # 결과 저장
    json_path = save_test_results("benchmark", results)
    markdown_path = generate_markdown_report("benchmark", results)

    print(f"\n{'=' * 80}")
    print("BENCHMARK TEST RESULTS")
    print(f"{'=' * 80}")
    print(f"Total Queries: {results['summary']['total_queries']}")
    print(f"Average Response Time: {results['summary']['avg_response_time']:.2f}s")
    print(f"Min Response Time: {results['summary']['min_response_time']:.2f}s")
    print(f"Max Response Time: {results['summary']['max_response_time']:.2f}s")
    if results["summary"]["avg_similarity"] is not None:
        print(f"Average Similarity: {results['summary']['avg_similarity']:.4f}")
        print(f"Min Similarity: {results['summary']['min_similarity']:.4f}")
        print(f"Max Similarity: {results['summary']['max_similarity']:.4f}")
    print("\nResults saved to:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {markdown_path}")
    print(f"{'=' * 80}\n")

    return results
