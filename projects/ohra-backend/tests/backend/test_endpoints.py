"""Backend API 엔드포인트 테스트"""

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
async def test_endpoints_availability():
    """주요 엔드포인트 가용성 테스트"""
    test_start = time.time()

    test_info = {
        "test_name": "Backend API 엔드포인트 테스트",
        "test_type": "backend",
        "is_evaluation_target": False,
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    print_test_header(
        test_info["test_name"], "주요 API 엔드포인트가 정상적으로 동작하는지 확인합니다.", is_evaluation_target=False
    )

    api_key = get_api_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    endpoints = [
        {
            "name": "chat/completions",
            "url": f"{BASE_URL}/v1/chat/completions",
            "method": "POST",
            "payload": {
                "model": "Qwen/Qwen3-4B-Instruct-2507",
                "messages": [{"role": "user", "content": "test"}],
            },
        },
        {"name": "embeddings", "url": f"{BASE_URL}/v1/embeddings", "method": "POST", "payload": {"input": "test"}},
        {"name": "models", "url": f"{BASE_URL}/v1/models", "method": "GET", "payload": None},
    ]

    results = []

    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            print(f"\n[TESTING] {endpoint['name']}...")

            try:
                start_time = time.time()

                if endpoint["method"] == "GET":
                    async with session.get(endpoint["url"], headers=headers) as response:
                        status = response.status
                        elapsed = time.time() - start_time
                else:
                    async with session.post(endpoint["url"], json=endpoint["payload"], headers=headers) as response:
                        status = response.status
                        elapsed = time.time() - start_time

                result = {
                    "endpoint": endpoint["name"],
                    "status": status,
                    "elapsed_time": elapsed,
                    "expected": 200,
                    "passed": status == 200,
                }

                results.append(result)
                print(f"  결과: Status={status}, Time={elapsed:.3f}s ({'✅ PASS' if status == 200 else '❌ FAIL'})")

            except Exception as e:
                results.append({"endpoint": endpoint["name"], "status": 0, "error": str(e), "passed": False})
                print(f"  결과: ERROR - {e}")

    passed_count = sum(1 for r in results if r.get("passed", False))
    total_count = len(results)

    test_info["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_info["total_duration"] = time.time() - test_start
    test_info["result"] = {
        "actual_value": f"{passed_count}/{total_count} 엔드포인트 정상 동작",
        "achieved": passed_count == total_count,
        "suitable": passed_count == total_count,
        "suitability_reason": "모든 엔드포인트 정상 동작" if passed_count == total_count else "일부 엔드포인트 실패",
    }
    test_info["details"] = {"results": results, "passed_count": passed_count, "total_count": total_count}

    print_test_summary(test_info)

    # 결과 저장
    output_dir = Path(__file__).parent.parent / "results"
    save_test_results("backend_endpoints", test_info, output_dir)

    return test_info
