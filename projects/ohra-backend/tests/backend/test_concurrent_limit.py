"""Backend API 동시 처리 한계 테스트"""
import pytest
import asyncio
import aiohttp
import time
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from tests.utils.api_client import make_chat_request
from tests.utils.test_helpers import (
    print_test_header,
    print_test_summary,
    save_test_results,
)


@pytest.mark.asyncio
async def test_concurrent_limit():
    """동시 처리 한계 탐색 테스트"""
    test_start = time.time()
    
    test_info = {
        "test_name": "Backend API 동시 처리 한계 테스트",
        "test_type": "backend",
        "is_evaluation_target": False,
        "started_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    print_test_header(
        test_info["test_name"],
        "동시 요청 수를 점진적으로 증가시켜 최대 동시 처리 가능 수를 확인합니다.",
        is_evaluation_target=False
    )
    
    query = "ai 아메바는 무슨일을 해"
    concurrent_counts = [5, 10, 20, 50, 100]
    
    print(f"[INFO] 테스트 쿼리: {query}")
    print(f"[INFO] 테스트할 동시 요청 수: {concurrent_counts}\n")
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        for count in concurrent_counts:
            print(f"\n[TESTING] 동시 요청 수: {count}")
            print(f"  요청 시작...")
            
            start_time = time.time()
            tasks = [
                make_chat_request(session, query)
                for _ in range(count)
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            elapsed = time.time() - start_time
            
            # 결과 분석
            success_count = sum(
                1 for r in responses
                if isinstance(r, dict) and r.get("status") == 200
            )
            failure_count = count - success_count
            success_rate = (success_count / count) * 100
            
            elapsed_times = [
                r.get("elapsed_time", 0)
                for r in responses
                if isinstance(r, dict) and r.get("status") == 200
            ]
            avg_response_time = sum(elapsed_times) / len(elapsed_times) if elapsed_times else 0
            
            test_result = {
                "concurrent_count": count,
                "success_count": success_count,
                "failure_count": failure_count,
                "success_rate": f"{success_rate:.1f}%",
                "avg_response_time": f"{avg_response_time:.3f}s",
                "total_elapsed_time": f"{elapsed:.3f}s"
            }
            
            results.append(test_result)
            
            print(f"  결과: 성공={success_count}/{count} ({success_rate:.1f}%), 평균 응답 시간={avg_response_time:.3f}s")
            
            # 실패율이 50% 이상이면 중단
            if success_rate < 50:
                print(f"  [WARNING] 성공률이 50% 미만이므로 테스트 중단")
                break
            
            # 요청 간 간격
            await asyncio.sleep(1)
    
    # 최종 결과
    valid_results = [r for r in results if float(r["success_rate"].rstrip("%")) >= 50]
    max_concurrent = max(r["concurrent_count"] for r in valid_results) if valid_results else 0
    
    test_info["completed_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    test_info["total_duration"] = time.time() - test_start
    test_info["results"] = results
    test_info["summary"] = {
        "max_concurrent_requests": max_concurrent,
        "recommended_concurrent_requests": min(max_concurrent, 20) if max_concurrent > 0 else 5
    }
    
    print_test_summary(test_info)
    
    print(f"\n[한계 테스트 결과]")
    print(f"최대 동시 처리 가능 수: {max_concurrent}")
    print(f"권장 동시 요청 수: {test_info['summary']['recommended_concurrent_requests']}")
    
    # 결과 저장
    output_dir = Path(__file__).parent.parent / "results"
    save_test_results("backend_concurrent_limit", test_info, output_dir)
    
    return test_info

