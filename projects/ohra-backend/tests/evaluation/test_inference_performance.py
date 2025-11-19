"""평가대상: 추론 성능 테스트"""

import pytest
import aiohttp
import time
from datetime import datetime
from pathlib import Path

from tests.utils.api_client import make_chat_request
from tests.utils.test_helpers import (
    print_test_header,
    print_test_summary,
    print_progress,
    save_test_results,
)


QUERY_SET = [
    "ai 아메바는 무슨일을 해",
    "어뷰징 경고 알림톡 수신자 필터 기능",
    "배포 프로세스는 어떻게 되나요",
    "Confluence 문서에서 API 명세를 찾아줘",
    "Jira 이슈에서 최근 결정 사항을 알려줘",
]


@pytest.mark.asyncio
async def test_inference_performance_basic():
    """평가대상: 기본 테스트 - 평균 추론 시간 2초 이내"""
    test_start = time.time()

    test_info = {
        "test_name": "추론 성능 테스트 - 기본",
        "test_type": "evaluation",
        "is_evaluation_target": True,
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target": {
            "description": "평균 LLM 추론 시간 2초 이내",
            "expected_value": "평균 추론 시간 < 2초",
            "threshold": "2.0초",
        },
    }

    print_test_header(
        test_info["test_name"],
        "평가대상: 5개 쿼리셋으로 평균 LLM 추론 시간이 2초 이내인지 확인합니다.",
        is_evaluation_target=True,
    )

    print(f"[INFO] 테스트 쿼리 수: {len(QUERY_SET)}")
    print("[INFO] 목표: 평균 LLM 추론 시간 < 2초\n")

    results = []

    async with aiohttp.ClientSession() as session:
        for i, query in enumerate(QUERY_SET, 1):
            print_progress(i, len(QUERY_SET), f"쿼리: {query[:50]}...")

            result = await make_chat_request(session, query)

            # 백엔드 로그에서 LLM 추론 시간을 추출할 수 없으므로
            # 전체 응답 시간의 95%를 추론 시간으로 추정
            # (실제로는 백엔드 로그 파싱 필요)
            total_time = result.get("elapsed_time", 0)
            inference_time = total_time * 0.95  # 추정값 (검색 시간 약 5% 가정)

            results.append(
                {
                    "query": query,
                    "inference_time": inference_time,
                    "total_time": total_time,
                    "status": result.get("status", 0),
                }
            )

            print(f"  LLM 추론 시간: {inference_time:.3f}s (추정)")

    inference_times = [r["inference_time"] for r in results if r["status"] == 200]

    if not inference_times:
        test_info["result"] = {
            "actual_value": "N/A (모든 요청 실패)",
            "achieved": False,
            "suitable": False,
            "suitability_reason": "모든 요청이 실패하여 측정 불가",
        }
    else:
        avg_inference_time = sum(inference_times) / len(inference_times)
        min_inference_time = min(inference_times)
        max_inference_time = max(inference_times)

        target_achieved = avg_inference_time < 2.0
        suitable = target_achieved and max_inference_time < 5.0

        test_info["result"] = {
            "actual_value": f"평균 {avg_inference_time:.3f}s (최소 {min_inference_time:.3f}s, 최대 {max_inference_time:.3f}s)",
            "achieved": target_achieved,
            "suitable": suitable,
            "suitability_reason": (
                "평균 추론 시간이 목표 이내이고 최대 시간도 합리적 범위"
                if suitable
                else "평균 또는 최대 추론 시간이 목표를 초과"
            ),
        }

        test_info["details"] = {
            "avg_inference_time": f"{avg_inference_time:.3f}s",
            "min_inference_time": f"{min_inference_time:.3f}s",
            "max_inference_time": f"{max_inference_time:.3f}s",
            "results": results,
        }

    test_info["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_info["total_duration"] = time.time() - test_start

    print_test_summary(test_info)

    # 결과 저장
    output_dir = Path(__file__).parent.parent / "results"
    save_test_results("inference_performance_basic", test_info, output_dir)

    return test_info


@pytest.mark.asyncio
async def test_input_token_limit():
    """Input 토큰 한계 테스트"""
    test_start = time.time()

    test_info = {
        "test_name": "추론 성능 테스트 - Input 토큰 한계",
        "test_type": "rag_pipeline",
        "is_evaluation_target": False,
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    print_test_header(
        test_info["test_name"],
        "입력 토큰 수를 점진적으로 증가시켜 최대 입력 토큰 수와 성능 변화를 확인합니다.",
        is_evaluation_target=False,
    )

    # 토큰 수에 맞는 텍스트 생성 (대략적인 추정)
    def generate_text_by_tokens(target_tokens: int) -> str:
        # 한국어 기준 대략 1토큰 = 1.5자 가정
        chars_per_token = 1.5
        target_chars = int(target_tokens * chars_per_token)
        return "안녕하세요. " * (target_chars // 10) + "테스트 질문입니다."

    token_counts = [100, 500, 1000, 2000, 4000, 8000, 16000]

    print(f"[INFO] 테스트할 토큰 수: {token_counts}")
    print("[INFO] 목표: 최대 입력 토큰 수 확인 및 성능 분석\n")

    results = []

    async with aiohttp.ClientSession() as session:
        for token_count in token_counts:
            print(f"\n[TESTING] 입력 토큰 수: {token_count}")

            long_text = generate_text_by_tokens(token_count)

            print("  요청 시작...")
            start_time = time.time()
            response = await make_chat_request(session, long_text)
            elapsed = time.time() - start_time

            if response.get("status") != 200:
                print(f"  [ERROR] 요청 실패: {response.get('error', 'Unknown error')}")
                break

            actual_tokens = response.get("usage", {}).get("prompt_tokens", 0)
            inference_time = elapsed * 0.95  # 추정값

            result = {
                "target_tokens": token_count,
                "actual_tokens": actual_tokens,
                "inference_time": inference_time,
                "total_time": elapsed,
                "tokens_per_second": actual_tokens / inference_time if inference_time > 0 else 0,
            }

            results.append(result)

            print(
                f"  결과: 실제 토큰={actual_tokens}, 추론 시간={inference_time:.3f}s, 속도={result['tokens_per_second']:.1f} tokens/s"
            )

    max_input_tokens = max(r["actual_tokens"] for r in results) if results else 0

    test_info["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_info["total_duration"] = time.time() - test_start
    test_info["results"] = results
    test_info["summary"] = {
        "max_input_tokens": max_input_tokens,
        "recommended_max_input_tokens": min(max_input_tokens, 4000) if max_input_tokens > 0 else 2000,
    }

    print_test_summary(test_info)

    print("\n[Input 토큰 한계 테스트 결과]")
    print(f"최대 입력 토큰 수: {max_input_tokens}")
    print(f"권장 최대 입력 토큰 수: {test_info['summary']['recommended_max_input_tokens']}")

    # 결과 저장
    output_dir = Path(__file__).parent.parent / "results"
    save_test_results("input_token_limit", test_info, output_dir)

    return test_info


@pytest.mark.asyncio
async def test_output_token_limit():
    """Output 토큰 한계 테스트"""
    test_start = time.time()

    test_info = {
        "test_name": "추론 성능 테스트 - Output 토큰 한계",
        "test_type": "rag_pipeline",
        "is_evaluation_target": False,
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    print_test_header(
        test_info["test_name"],
        "출력 토큰 수를 점진적으로 증가시켜 최대 출력 토큰 수와 생성 속도를 확인합니다.",
        is_evaluation_target=False,
    )

    query = "배포 프로세스에 대해 자세히 설명해줘"
    max_tokens_list = [100, 500, 1000, 2000, 4000, 8000]

    print(f"[INFO] 테스트 쿼리: {query}")
    print(f"[INFO] 테스트할 max_tokens: {max_tokens_list}\n")

    results = []

    async with aiohttp.ClientSession() as session:
        for max_tokens in max_tokens_list:
            print(f"\n[TESTING] max_tokens: {max_tokens}")

            print("  요청 시작...")
            start_time = time.time()
            response = await make_chat_request(session, query, max_tokens=max_tokens)
            elapsed = time.time() - start_time

            if response.get("status") != 200:
                print(f"  [ERROR] 요청 실패: {response.get('error', 'Unknown error')}")
                break

            actual_tokens = response.get("usage", {}).get("completion_tokens", 0)
            inference_time = elapsed * 0.95  # 추정값

            result = {
                "max_tokens": max_tokens,
                "actual_tokens": actual_tokens,
                "generation_time": inference_time,
                "total_time": elapsed,
                "tokens_per_second": actual_tokens / inference_time if inference_time > 0 else 0,
            }

            results.append(result)

            print(
                f"  결과: 실제 토큰={actual_tokens}, 생성 시간={inference_time:.3f}s, 속도={result['tokens_per_second']:.1f} tokens/s"
            )

    max_output_tokens = max(r["actual_tokens"] for r in results) if results else 0

    test_info["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_info["total_duration"] = time.time() - test_start
    test_info["results"] = results
    test_info["summary"] = {
        "max_output_tokens": max_output_tokens,
        "recommended_max_output_tokens": min(max_output_tokens, 2000) if max_output_tokens > 0 else 1000,
    }

    print_test_summary(test_info)

    print("\n[Output 토큰 한계 테스트 결과]")
    print(f"최대 출력 토큰 수: {max_output_tokens}")
    print(f"권장 최대 출력 토큰 수: {test_info['summary']['recommended_max_output_tokens']}")

    # 결과 저장
    output_dir = Path(__file__).parent.parent / "results"
    save_test_results("output_token_limit", test_info, output_dir)

    return test_info
