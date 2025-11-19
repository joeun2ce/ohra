"""LLM 응답 품질 테스트"""

import pytest
import aiohttp
import time
from datetime import datetime
from pathlib import Path

from tests.utils.api_client import make_chat_request
from tests.utils.test_helpers import (
    print_test_header,
    print_test_summary,
    save_test_results,
)


QUERY_SET = [
    "ai 아메바는 무슨일을 해",
    "배포 프로세스는 어떻게 되나요",
    "Confluence 문서에서 API 명세를 찾아줘",
]


@pytest.mark.asyncio
async def test_response_quality():
    """LLM 응답 품질 테스트"""
    test_start = time.time()

    test_info = {
        "test_name": "LLM 응답 품질 테스트",
        "test_type": "llm",
        "is_evaluation_target": False,
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    print_test_header(
        test_info["test_name"], "LLM 응답의 관련성, 일관성, 품질을 확인합니다.", is_evaluation_target=False
    )

    print(f"[INFO] 테스트 쿼리 수: {len(QUERY_SET)}\n")

    results = []

    async with aiohttp.ClientSession() as session:
        for i, query in enumerate(QUERY_SET, 1):
            print(f"[TESTING] 쿼리 {i}/{len(QUERY_SET)}: {query[:50]}...")

            response = await make_chat_request(session, query)
            response_text = response.get("response_text", "")

            # 간단한 품질 체크
            has_content = len(response_text) > 10
            is_relevant = len(response_text) > 20  # 충분한 길이면 관련성 있다고 간주

            results.append(
                {
                    "query": query,
                    "status": response.get("status", 0),
                    "response_length": len(response_text),
                    "has_content": has_content,
                    "is_relevant": is_relevant,
                    "response_preview": response_text[:100] + "..." if len(response_text) > 100 else response_text,
                }
            )

            print(f"  결과: Status={response.get('status', 0)}, 길이={len(response_text)}자")

    success_count = sum(1 for r in results if r["status"] == 200)
    quality_count = sum(1 for r in results if r.get("is_relevant", False))

    test_info["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_info["total_duration"] = time.time() - test_start
    test_info["result"] = {
        "actual_value": f"성공: {success_count}/{len(QUERY_SET)}, 품질: {quality_count}/{len(QUERY_SET)}",
        "achieved": success_count == len(QUERY_SET),
        "suitable": success_count == len(QUERY_SET) and quality_count == len(QUERY_SET),
        "suitability_reason": (
            "모든 응답 성공 및 품질 양호"
            if (success_count == len(QUERY_SET) and quality_count == len(QUERY_SET))
            else "일부 응답 실패 또는 품질 저하"
        ),
    }
    test_info["details"] = {"results": results, "success_count": success_count, "quality_count": quality_count}

    print_test_summary(test_info)

    # 결과 저장
    output_dir = Path(__file__).parent.parent / "results"
    save_test_results("llm_response_quality", test_info, output_dir)

    return test_info
