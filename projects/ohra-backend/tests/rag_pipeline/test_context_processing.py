"""RAG Pipeline 컨텍스트 처리 테스트"""
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


@pytest.mark.asyncio
async def test_context_processing():
    """컨텍스트 처리 테스트"""
    test_start = time.time()
    
    test_info = {
        "test_name": "RAG Pipeline 컨텍스트 처리 테스트",
        "test_type": "rag_pipeline",
        "is_evaluation_target": False,
        "started_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    print_test_header(
        test_info["test_name"],
        "검색된 문서가 컨텍스트로 포함되어 응답에 반영되는지 확인합니다.",
        is_evaluation_target=False
    )
    
    queries = [
        "배포 프로세스는 어떻게 되나요",
        "Confluence 문서에서 API 명세를 찾아줘",
    ]
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        for query in queries:
            print(f"\n[TESTING] 쿼리: {query}")
            
            response = await make_chat_request(session, query)
            response_text = response.get("response_text", "")
            
            # 컨텍스트 포함 여부 확인 (간단한 휴리스틱)
            # 실제로는 백엔드 로그에서 검색된 문서 확인 필요
            has_context = len(response_text) > 50  # 응답이 충분히 길면 컨텍스트 포함으로 간주
            
            results.append({
                "query": query,
                "status": response.get("status", 0),
                "response_length": len(response_text),
                "has_context": has_context,
            })
            
            print(f"  결과: Status={response.get('status', 0)}, 길이={len(response_text)}자, 컨텍스트 포함={'예' if has_context else '불확실'}")
    
    test_info["completed_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    test_info["total_duration"] = time.time() - test_start
    test_info["details"] = {
        "results": results
    }
    
    print_test_summary(test_info)
    
    # 결과 저장
    output_dir = Path(__file__).parent.parent / "results"
    save_test_results("rag_pipeline_context_processing", test_info, output_dir)
    
    return test_info

