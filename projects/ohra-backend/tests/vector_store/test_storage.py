"""Vector Store 저장/조회 테스트"""

import pytest
from datetime import datetime
from pathlib import Path

from tests.utils.test_helpers import (
    print_test_header,
    print_test_summary,
    save_test_results,
)


@pytest.mark.asyncio
async def test_vector_storage():
    """Vector Store 저장/조회 테스트"""
    test_start = datetime.now()

    test_info = {
        "test_name": "Vector Store 저장/조회 테스트",
        "test_type": "vector_store",
        "is_evaluation_target": False,
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    print_test_header(
        test_info["test_name"],
        "벡터 저장소에 문서가 저장되고 조회되는지 확인합니다. (실제 구현 필요)",
        is_evaluation_target=False,
    )

    # TODO: 실제 Qdrant 연결 및 저장/조회 테스트
    # from ohra.shared_kernel.infra.qdrant import QdrantAdapter

    test_info["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_info["total_duration"] = (datetime.now() - test_start).total_seconds()
    test_info["result"] = {
        "actual_value": "테스트 미구현",
        "achieved": False,
        "suitable": False,
        "suitability_reason": "실제 Qdrant 연결 및 테스트 구현 필요",
    }

    print_test_summary(test_info)

    # 결과 저장
    output_dir = Path(__file__).parent.parent / "results"
    save_test_results("vector_store_storage", test_info, output_dir)

    return test_info
