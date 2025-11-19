"""Worker 테스트 헬퍼 (백엔드와 동일한 구조)"""

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


def print_test_header(test_name: str, description: str, is_evaluation_target: bool = False):
    """테스트 시작 헤더 출력"""
    print("\n" + "=" * 80)
    print(f"TEST: {test_name}")
    if is_evaluation_target:
        print("📊 평가대상: YES")
    print("=" * 80)
    print(f"Description: {description}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")


def print_test_summary(test_info: Dict[str, Any]):
    """테스트 요약 출력"""
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Test Name: {test_info.get('test_name', 'Unknown')}")
    print(f"Test Type: {test_info.get('test_type', 'Unknown')}")
    if test_info.get("is_evaluation_target"):
        print("📊 평가대상: YES")
    print(f"Started: {test_info.get('started_at', 'Unknown')}")
    print(f"Completed: {test_info.get('completed_at', 'Unknown')}")
    print(f"Total Duration: {test_info.get('total_duration', 0):.2f}s")

    if "target" in test_info and "result" in test_info:
        print("\n" + "-" * 80)
        print("TARGET vs RESULT")
        print("-" * 80)
        target = test_info["target"]
        result = test_info["result"]

        print(f"목표: {target.get('description', 'N/A')}")
        print(f"기대값: {target.get('expected_value', 'N/A')}")
        print(f"실제값: {result.get('actual_value', 'N/A')}")

        achieved = result.get("achieved", False)
        suitable = result.get("suitable", False)

        print(f"달성 여부: {'✅ 달성' if achieved else '❌ 미달성'}")
        print(f"적합성: {'✅ 적합' if suitable else '⚠️ 부적합'}")

        if result.get("suitability_reason"):
            print(f"적합성 평가: {result['suitability_reason']}")

    print("=" * 80 + "\n")


def save_test_results(test_name: str, results: Dict[str, Any], output_dir: Path = None) -> Path:
    """테스트 결과를 JSON 파일로 저장"""
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "results"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{test_name}_{timestamp}.json"
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return filepath
