"""pytest 설정 및 공통 fixture"""
import pytest
import sqlite3
import uuid
import hashlib
import secrets
import os
from pathlib import Path
from datetime import datetime


@pytest.fixture(scope="session", autouse=True)
def setup_test_api_key():
    """테스트 세션 시작 시 API 키 생성, 종료 시 삭제 (Backend 전용)"""
    # tests/conftest.py -> projects/ohra-backend/
    project_root = Path(__file__).parent.parent
    # projects/ohra-backend/data/database.db
    db_path = project_root / "data" / "database.db"
    
    if not db_path.exists():
        pytest.skip(f"Database not found at {db_path}. Please run migrations first.")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 테스트용 사용자 생성 또는 가져오기
    test_email = "pytest-test@ohra.local"
    cursor.execute('SELECT id, email FROM ohra_user WHERE email = ?', (test_email,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        user_id = existing_user[0]
    else:
        user_id = str(uuid.uuid4())
        now = datetime.now()
        cursor.execute(
            'INSERT INTO ohra_user (id, email, name, is_active, is_admin, external_user_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (user_id, test_email, "Pytest Test User", True, False, None, now, now)
        )
        conn.commit()
    
    # API 키 생성
    api_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    key_id = str(uuid.uuid4())
    now = datetime.now()
    
    # 기존 API 키 삭제 (같은 이름의 키)
    cursor.execute('DELETE FROM ohra_api_key WHERE user_id = ? AND name = ?', (user_id, "Pytest Test API Key"))
    
    # 새 API 키 삽입
    cursor.execute(
        'INSERT INTO ohra_api_key (id, user_id, key_hash, name, expires_at, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (key_id, user_id, key_hash, "Pytest Test API Key", None, True, now, now)
    )
    conn.commit()
    
    # 환경변수에 설정
    os.environ["OHRA_API_KEY"] = api_key
    
    print(f"\n[TEST SETUP] API Key created: {api_key[:20]}...")
    print(f"[TEST SETUP] Key ID: {key_id}")
    
    yield api_key
    
    # 테스트 종료 후 정리
    print(f"\n[TEST TEARDOWN] Cleaning up API key...")
    cursor.execute('DELETE FROM ohra_api_key WHERE id = ?', (key_id,))
    conn.commit()
    conn.close()
    
    # 환경변수에서 제거
    if "OHRA_API_KEY" in os.environ:
        del os.environ["OHRA_API_KEY"]
    
    print(f"[TEST TEARDOWN] API Key deleted: {key_id}")

