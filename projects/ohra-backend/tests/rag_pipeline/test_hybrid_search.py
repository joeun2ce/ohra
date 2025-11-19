"""RAG Pipeline 하이브리드 검색 테스트"""
import pytest
import aiohttp
import time
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from tests.utils.api_client import make_chat_request
from tests.utils.test_helpers import (
    print_test_header,
    print_test_summary,
    save_test_results,
)


QUERY_SET = [
    "ai 아메바는 무슨일을 해",
    "어뷰징 경고 알림톡 수신자 필터 기능",
    "배포 프로세스는 어떻게 되나요",
]


@pytest.mark.asyncio
async def test_hybrid_search_comparison():
    """하이브리드 검색 vs 단일 검색 비교 테스트"""
    test_start = time.time()
    
    test_info = {
        "test_name": "RAG Pipeline 하이브리드 검색 테스트",
        "test_type": "rag_pipeline",
        "is_evaluation_target": False,
        "started_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    print_test_header(
        test_info["test_name"],
        "하이브리드 검색(벡터 + BM25)과 단일 검색의 성능 및 품질을 비교합니다.",
        is_evaluation_target=False
    )
    
    print(f"[INFO] 테스트 쿼리 수: {len(QUERY_SET)}\n")
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        for i, query in enumerate(QUERY_SET, 1):
            print(f"[TESTING] 쿼리 {i}/{len(QUERY_SET)}: {query[:50]}...")
            
            # 하이브리드 검색 (기본)
            start_time = time.time()
            response = await make_chat_request(session, query)
            elapsed = time.time() - start_time
            
            results.append({
                "query": query,
                "status": response.get("status", 0),
                "response_time": elapsed,
                "response_length": len(response.get("response_text", "")),
            })
            
            print(f"  결과: Status={response.get('status', 0)}, Time={elapsed:.3f}s")
    
    success_count = sum(1 for r in results if r["status"] == 200)
    avg_response_time = sum(r["response_time"] for r in results) / len(results) if results else 0
    
    test_info["completed_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    test_info["total_duration"] = time.time() - test_start
    test_info["result"] = {
        "actual_value": f"성공: {success_count}/{len(QUERY_SET)}, 평균 응답 시간: {avg_response_time:.3f}s",
        "achieved": success_count == len(QUERY_SET),
        "suitable": success_count == len(QUERY_SET) and avg_response_time < 3.0,
        "suitability_reason": (
            "모든 쿼리 성공 및 응답 시간 적절"
            if (success_count == len(QUERY_SET) and avg_response_time < 3.0)
            else "일부 쿼리 실패 또는 응답 시간 초과"
        )
    }
    test_info["details"] = {
        "results": results,
        "success_count": success_count,
        "avg_response_time": avg_response_time
    }
    
    print_test_summary(test_info)
    
    # 결과 저장
    output_dir = Path(__file__).parent.parent / "results"
    save_test_results("rag_pipeline_hybrid_search", test_info, output_dir)
    
    return test_info

