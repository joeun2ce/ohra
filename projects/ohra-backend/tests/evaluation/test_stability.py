"""평가대상: 안정성 테스트 - 동시 요청 처리"""
import pytest
import asyncio
import aiohttp
import time
import os
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from tests.utils.api_client import make_chat_request, BASE_URL
from tests.utils.test_helpers import (
    print_test_header,
    print_test_summary,
    print_progress,
    save_test_results,
)


@pytest.mark.asyncio
async def test_stability_basic():
    """평가대상: 기본 테스트 - 동시 5개 요청 처리"""
    test_start = time.time()
    
    test_info = {
        "test_name": "안정성 테스트 - 기본 (동시 5개 요청)",
        "test_type": "evaluation",
        "is_evaluation_target": True,
        "started_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "target": {
            "description": "동시 5개 요청 처리",
            "expected_value": "성공률 100%, 평균 응답 시간 < 3초",
            "threshold": "성공률 100%"
        }
    }
    
    print_test_header(
        test_info["test_name"],
        "평가대상: 동시 5개 요청을 발송하여 모든 요청이 정상 처리되는지 확인합니다.",
        is_evaluation_target=True
    )
    
    query = "ai 아메바는 무슨일을 해"
    concurrent_count = 5
    
    print(f"[INFO] 동시 요청 수: {concurrent_count}")
    print(f"[INFO] 테스트 쿼리: {query}")
    print(f"[INFO] 요청 시작...\n")
    
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        tasks = [
            make_chat_request(session, query)
            for _ in range(concurrent_count)
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
    elapsed = time.time() - start_time
    
    # 결과 분석
    success_count = sum(
        1 for r in responses
        if isinstance(r, dict) and r.get("status") == 200
    )
    failure_count = concurrent_count - success_count
    success_rate = (success_count / concurrent_count) * 100
    
    elapsed_times = [
        r.get("elapsed_time", 0)
        for r in responses
        if isinstance(r, dict) and r.get("status") == 200
    ]
    avg_response_time = sum(elapsed_times) / len(elapsed_times) if elapsed_times else 0
    min_response_time = min(elapsed_times) if elapsed_times else 0
    max_response_time = max(elapsed_times) if elapsed_times else 0
    
    # 목표 달성 여부
    target_achieved = success_rate == 100
    suitable = target_achieved and avg_response_time < 3.0
    
    test_info["result"] = {
        "actual_value": f"성공률 {success_rate:.1f}%, 평균 응답 시간 {avg_response_time:.3f}s",
        "achieved": target_achieved,
        "suitable": suitable,
        "suitability_reason": (
            "모든 요청이 성공하고 응답 시간이 목표 이내"
            if suitable
            else "성공률 또는 응답 시간이 목표를 초과"
        )
    }
    
    test_info["completed_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    test_info["total_duration"] = time.time() - test_start
    test_info["details"] = {
        "concurrent_count": concurrent_count,
        "total_requests": concurrent_count,
        "success_count": success_count,
        "failure_count": failure_count,
        "success_rate": f"{success_rate:.1f}%",
        "avg_response_time": f"{avg_response_time:.3f}s",
        "min_response_time": f"{min_response_time:.3f}s",
        "max_response_time": f"{max_response_time:.3f}s",
        "total_elapsed_time": f"{elapsed:.3f}s",
        "responses": [
            {
                "index": i + 1,
                "status": r.get("status", "ERROR") if isinstance(r, dict) else "EXCEPTION",
                "elapsed_time": r.get("elapsed_time", 0) if isinstance(r, dict) else 0,
                "error": str(r) if not isinstance(r, dict) else None
            }
            for i, r in enumerate(responses)
        ]
    }
    
    print_test_summary(test_info)
    
    # 상세 결과 출력
    print("\n[상세 결과]")
    for i, response in enumerate(responses, 1):
        if isinstance(response, dict):
            status = response.get("status", "N/A")
            elapsed = response.get("elapsed_time", 0)
            print(f"  요청 {i}: Status={status}, Time={elapsed:.3f}s")
        else:
            print(f"  요청 {i}: ERROR - {str(response)}")
    
    # 결과 저장
    output_dir = Path(__file__).parent.parent / "results"
    save_test_results("stability_basic", test_info, output_dir)
    
    return test_info


@pytest.mark.asyncio
async def test_stability_limit():
    """한계 테스트: 동시 처리 한계 탐색"""
    test_start = time.time()
    
    test_info = {
        "test_name": "안정성 테스트 - 한계 탐색",
        "test_type": "evaluation",
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
                "min_response_time": f"{min(elapsed_times):.3f}s" if elapsed_times else "N/A",
                "max_response_time": f"{max(elapsed_times):.3f}s" if elapsed_times else "N/A",
                "total_elapsed_time": f"{elapsed:.3f}s"
            }
            
            results.append(test_result)
            
            print(f"  결과: 성공={success_count}/{count} ({success_rate:.1f}%), 평균 응답 시간={avg_response_time:.3f}s")
            
            # 실패율이 50% 이상이면 중단
            if success_rate < 50:
                print(f"  [WARNING] 성공률이 50% 미만이므로 테스트 중단")
                break
            
            # 요청 간 간격 (서버 부하 방지)
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
    save_test_results("stability_limit", test_info, output_dir)
    
    return test_info

