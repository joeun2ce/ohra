"""Backend API 에러 핸들링 테스트"""

import pytest
import aiohttp
import time
from datetime import datetime
from pathlib import Path

from tests.utils.api_client import BASE_URL, get_api_key
from tests.utils.test_helpers import (
    print_test_header,
    print_test_summary,
    save_test_results,
)


@pytest.mark.asyncio
async def test_error_handling():
    """에러 핸들링 테스트"""
    test_start = time.time()

    test_info = {
        "test_name": "Backend API 에러 핸들링 테스트",
        "test_type": "backend",
        "is_evaluation_target": False,
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    print_test_header(
        test_info["test_name"],
        "잘못된 요청 형식, 필수 파라미터 누락 등에 대한 에러 처리가 정상 동작하는지 확인합니다.",
        is_evaluation_target=False,
    )

    api_key = get_api_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    error_cases = [
        {
            "name": "필수 파라미터 누락 (messages)",
            "url": f"{BASE_URL}/v1/chat/completions",
            "payload": {
                "model": "Qwen/Qwen3-4B-Instruct-2507",
            },
            "expected_status": [400, 422],
        },
        {
            "name": "잘못된 모델 이름",
            "url": f"{BASE_URL}/v1/chat/completions",
            "payload": {
                "model": "invalid-model-name",
                "messages": [{"role": "user", "content": "test"}],
            },
            "expected_status": [400, 404, 422],
        },
        {
            "name": "잘못된 JSON 형식",
            "url": f"{BASE_URL}/v1/chat/completions",
            "payload": "invalid json",
            "expected_status": [400, 422],
        },
        {
            "name": "임베딩 - 필수 파라미터 누락 (input)",
            "url": f"{BASE_URL}/v1/embeddings",
            "payload": {},
            "expected_status": [400, 422],
        },
    ]

    results = []

    async with aiohttp.ClientSession() as session:
        for case in error_cases:
            print(f"\n[TESTING] {case['name']}...")

            try:
                if isinstance(case["payload"], str):
                    # 잘못된 JSON 형식
                    async with session.post(case["url"], data=case["payload"], headers=headers) as response:
                        status = response.status
                else:
                    async with session.post(case["url"], json=case["payload"], headers=headers) as response:
                        status = response.status

                expected = case["expected_status"]
                passed = status in expected

                result = {"test": case["name"], "status": status, "expected_status": expected, "passed": passed}

                results.append(result)
                print(f"  결과: Status={status}, Expected={expected} ({'✅ PASS' if passed else '❌ FAIL'})")

            except Exception as e:
                results.append({"test": case["name"], "status": 0, "error": str(e), "passed": False})
                print(f"  결과: ERROR - {e}")

    passed_count = sum(1 for r in results if r.get("passed", False))
    total_count = len(results)

    test_info["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_info["total_duration"] = time.time() - test_start
    test_info["result"] = {
        "actual_value": f"{passed_count}/{total_count} 에러 케이스 정상 처리",
        "achieved": passed_count == total_count,
        "suitable": passed_count == total_count,
        "suitability_reason": "모든 에러 케이스 정상 처리"
        if passed_count == total_count
        else "일부 에러 케이스 처리 실패",
    }
    test_info["details"] = {"results": results, "passed_count": passed_count, "total_count": total_count}

    print_test_summary(test_info)

    # 결과 저장
    output_dir = Path(__file__).parent.parent / "results"
    save_test_results("backend_error_handling", test_info, output_dir)

    return test_info
