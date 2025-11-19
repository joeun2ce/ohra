"""Embedding 품질 테스트"""
import pytest
import aiohttp
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from tests.utils.api_client import make_embedding_request
from tests.utils.test_helpers import (
    print_test_header,
    print_test_summary,
    save_test_results,
)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """코사인 유사도 계산"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot_product / (norm1 * norm2))


@pytest.mark.asyncio
async def test_embedding_quality():
    """임베딩 품질 테스트"""
    test_start = datetime.now()
    
    test_info = {
        "test_name": "Embedding 품질 테스트",
        "test_type": "embedding",
        "is_evaluation_target": False,
        "started_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    print_test_header(
        test_info["test_name"],
        "유사한 텍스트의 임베딩 유사도가 높고, 다른 텍스트의 유사도가 낮은지 확인합니다.",
        is_evaluation_target=False
    )
    
    test_pairs = [
        {
            "text1": "AI 아메바는 질문 생성 기능을 제공합니다",
            "text2": "AI 아메바는 질문을 생성하는 기능이 있습니다",
            "expected_similar": True,
            "description": "유사한 의미"
        },
        {
            "text1": "AI 아메바는 질문 생성 기능을 제공합니다",
            "text2": "배포 프로세스는 어떻게 되나요",
            "expected_similar": False,
            "description": "다른 주제"
        },
    ]
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        for i, pair in enumerate(test_pairs, 1):
            print(f"\n[TESTING] 쌍 {i}: {pair['description']}")
            
            embedding1 = await make_embedding_request(session, pair["text1"])
            embedding2 = await make_embedding_request(session, pair["text2"])
            
            if embedding1 and embedding2:
                similarity = cosine_similarity(
                    embedding1.get("embedding", []),
                    embedding2.get("embedding", [])
                )
                
                expected = pair["expected_similar"]
                passed = (similarity > 0.7) == expected
                
                result = {
                    "text1": pair["text1"],
                    "text2": pair["text2"],
                    "similarity": similarity,
                    "expected_similar": expected,
                    "passed": passed
                }
                
                results.append(result)
                print(f"  결과: 유사도={similarity:.4f}, 예상={'유사' if expected else '다름'} ({'✅ PASS' if passed else '❌ FAIL'})")
            else:
                results.append({
                    "text1": pair["text1"],
                    "text2": pair["text2"],
                    "error": "임베딩 생성 실패",
                    "passed": False
                })
                print(f"  결과: ERROR - 임베딩 생성 실패")
    
    passed_count = sum(1 for r in results if r.get("passed", False))
    total_count = len(results)
    
    test_info["completed_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    test_info["total_duration"] = (datetime.now() - test_start).total_seconds()
    test_info["result"] = {
        "actual_value": f"{passed_count}/{total_count} 테스트 통과",
        "achieved": passed_count == total_count,
        "suitable": passed_count == total_count,
        "suitability_reason": "모든 임베딩 품질 테스트 통과" if passed_count == total_count else "일부 테스트 실패"
    }
    test_info["details"] = {
        "results": results,
        "passed_count": passed_count,
        "total_count": total_count
    }
    
    print_test_summary(test_info)
    
    # 결과 저장
    output_dir = Path(__file__).parent.parent / "results"
    save_test_results("embedding_quality", test_info, output_dir)
    
    return test_info

