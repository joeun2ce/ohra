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
    if test_info.get('is_evaluation_target'):
        print("📊 평가대상: YES")
    print(f"Started: {test_info.get('started_at', 'Unknown')}")
    print(f"Completed: {test_info.get('completed_at', 'Unknown')}")
    print(f"Total Duration: {test_info.get('total_duration', 0):.2f}s")
    
    if 'target' in test_info and 'result' in test_info:
        print("\n" + "-" * 80)
        print("TARGET vs RESULT")
        print("-" * 80)
        target = test_info['target']
        result = test_info['result']
        
        print(f"목표: {target.get('description', 'N/A')}")
        print(f"기대값: {target.get('expected_value', 'N/A')}")
        print(f"실제값: {result.get('actual_value', 'N/A')}")
        
        achieved = result.get('achieved', False)
        suitable = result.get('suitable', False)
        
        print(f"달성 여부: {'✅ 달성' if achieved else '❌ 미달성'}")
        print(f"적합성: {'✅ 적합' if suitable else '⚠️ 부적합'}")
        
        if result.get('suitability_reason'):
            print(f"적합성 평가: {result['suitability_reason']}")
    
    print("=" * 80 + "\n")


def print_progress(current: int, total: int, message: str = ""):
    """진행 상황 출력"""
    print(f"[{current}/{total}] {message}")


def print_section(title: str):
    """섹션 구분선 출력"""
    print(f"\n{'=' * 80}")
    print(title)
    print("=" * 80)


def save_test_results(test_name: str, results: Dict[str, Any], output_dir: Path = None) -> Path:
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "results"
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{test_name}_{timestamp}.json"
    filepath = output_dir / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return filepath


def generate_markdown_report(test_name: str, results: Dict[str, Any], output_dir: Path = None) -> Path:
    """벤치마크 결과를 마크다운 보고서로 생성"""
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "results"
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{test_name}_{timestamp}.md"
    filepath = output_dir / filename
    
    summary = results.get("summary", {})
    queries = results.get("queries", [])
    
    markdown = f"""# 벤치마크 테스트 결과 보고서

## 테스트 정보
- **테스트 이름**: {results.get('test_name', 'Unknown')}
- **실행 시간**: {results.get('timestamp', 'Unknown')}
- **총 쿼리 수**: {summary.get('total_queries', 0)}

## 성능 요약

### 응답 시간
- **평균 응답 시간**: {summary.get('avg_response_time', 0):.2f}초
- **최소 응답 시간**: {summary.get('min_response_time', 0):.2f}초
- **최대 응답 시간**: {summary.get('max_response_time', 0):.2f}초

"""
    
    if summary.get('avg_similarity') is not None:
        markdown += f"""### 임베딩 유사도
- **평균 유사도**: {summary.get('avg_similarity', 0):.4f}
- **최소 유사도**: {summary.get('min_similarity', 0):.4f}
- **최대 유사도**: {summary.get('max_similarity', 0):.4f}

"""
    
    markdown += """## 상세 결과

"""
    
    for i, query_result in enumerate(queries, 1):
        query = query_result.get("query", "")
        elapsed = query_result.get("elapsed_time", 0)
        status = query_result.get("status", 0)
        response_text = query_result.get("response_text", "")
        quality = query_result.get("embedding_quality", {})
        
        markdown += f"""### 쿼리 {i}: {query}

- **응답 시간**: {elapsed:.2f}초
- **HTTP 상태**: {status}
- **응답 길이**: {len(response_text)}자

"""
        
        if quality.get("similarity") is not None:
            markdown += f"""- **임베딩 유사도**: {quality.get('similarity', 0):.4f}

"""
        
        if response_text:
            # 응답 텍스트를 요약 (처음 200자만)
            preview = response_text[:200] + "..." if len(response_text) > 200 else response_text
            markdown += f"""**응답 미리보기**:
```
{preview}
```

"""
        
        markdown += "\n---\n\n"
    
    markdown += f"""
## 메타데이터

- 생성 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- 원본 JSON 파일: `{test_name}_{timestamp}.json`
"""
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown)
    
    return filepath

