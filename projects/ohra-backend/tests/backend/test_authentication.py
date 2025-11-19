"""Backend API 인증/인가 테스트"""

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
async def test_api_key_validation():
    """API 키 검증 테스트"""
    test_start = time.time()

    test_info = {
        "test_name": "Backend API 인증 테스트 - API 키 검증",
        "test_type": "backend",
        "is_evaluation_target": False,
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    print_test_header(
        test_info["test_name"],
        "유효한 API 키와 무효한 API 키로 요청을 보내 검증이 정상 동작하는지 확인합니다.",
        is_evaluation_target=False,
    )

    results = []

    async with aiohttp.ClientSession() as session:
        # 1. 유효한 API 키로 요청
        print("[TESTING] 유효한 API 키로 요청...")
        try:
            api_key = get_api_key()
            url = f"{BASE_URL}/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "Qwen/Qwen3-4B-Instruct-2507",
                "messages": [{"role": "user", "content": "test"}],
            }

            async with session.post(url, json=payload, headers=headers) as response:
                status = response.status
                results.append({"test": "valid_api_key", "status": status, "expected": 200, "passed": status == 200})
                print(f"  결과: Status={status} ({'✅ PASS' if status == 200 else '❌ FAIL'})")
        except Exception as e:
            results.append({"test": "valid_api_key", "status": 0, "error": str(e), "passed": False})
            print(f"  결과: ERROR - {e}")

        # 2. 무효한 API 키로 요청
        print("\n[TESTING] 무효한 API 키로 요청...")
        try:
            invalid_key = "invalid-api-key-12345"
            headers = {
                "Authorization": f"Bearer {invalid_key}",
                "Content-Type": "application/json",
            }

            async with session.post(url, json=payload, headers=headers) as response:
                status = response.status
                results.append({"test": "invalid_api_key", "status": status, "expected": 401, "passed": status == 401})
                print(f"  결과: Status={status} ({'✅ PASS' if status == 401 else '❌ FAIL'})")
        except Exception as e:
            results.append({"test": "invalid_api_key", "status": 0, "error": str(e), "passed": False})
            print(f"  결과: ERROR - {e}")

        # 3. API 키 없이 요청
        print("\n[TESTING] API 키 없이 요청...")
        try:
            headers = {
                "Content-Type": "application/json",
            }

            async with session.post(url, json=payload, headers=headers) as response:
                status = response.status
                results.append({"test": "no_api_key", "status": status, "expected": 401, "passed": status == 401})
                print(f"  결과: Status={status} ({'✅ PASS' if status == 401 else '❌ FAIL'})")
        except Exception as e:
            results.append({"test": "no_api_key", "status": 0, "error": str(e), "passed": False})
            print(f"  결과: ERROR - {e}")

    passed_count = sum(1 for r in results if r.get("passed", False))
    total_count = len(results)

    test_info["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_info["total_duration"] = time.time() - test_start
    test_info["result"] = {
        "actual_value": f"{passed_count}/{total_count} 테스트 통과",
        "achieved": passed_count == total_count,
        "suitable": passed_count == total_count,
        "suitability_reason": "모든 인증 테스트 통과" if passed_count == total_count else "일부 인증 테스트 실패",
    }
    test_info["details"] = {"results": results, "passed_count": passed_count, "total_count": total_count}

    print_test_summary(test_info)

    # 결과 저장
    output_dir = Path(__file__).parent.parent / "results"
    save_test_results("backend_authentication", test_info, output_dir)

    return test_info
