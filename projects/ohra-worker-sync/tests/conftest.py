"""pytest 설정 및 공통 fixture (Worker)"""

import pytest
from pathlib import Path


@pytest.fixture(scope="session", autouse=True)
def setup_worker_test():
    """워커 테스트 세션 설정"""
    # Worker 프로젝트 루트
    project_root = Path(__file__).parent.parent

    print(f"\n[WORKER TEST SETUP] Project root: {project_root}")

    yield

    print("\n[WORKER TEST TEARDOWN] Cleaning up...")
