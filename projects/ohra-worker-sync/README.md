# ohra-worker-sync

```bash
# 기본 실행 (24시간 전부터 동기화)
uv run python -m ohra.workers.sync.main all

# 특정 날짜부터 동기화
uv run python -m ohra.workers.sync.main all --since 2025-01-01

# 주기적 실행 (매 6시간마다)
uv run python -m ohra.workers.sync.main all --schedule 6

# 특정 플랫폼만 동기화
uv run python -m ohra.workers.sync.main confluence
uv run python -m ohra.workers.sync.main jira
```

## architecture

```bash
main.py (진입점)
  ↓
sync_job() → confluence.main() / jira.main() (데코레이터로 감싸진 함수)
  ↓
base.py의 sync_script 데코레이터
  ↓
[1단계: Extract] extract_documents() → 문서를 하나씩 yield
  ↓
[2단계: 변경 감지] base.py에서 version_key 기반 변경 감지
  - get_by_filter()로 기존 문서 조회
  - version_key 비교
  - 같으면 skip
  - 다르면 delete_by_filter()로 기존 청크 삭제
  ↓
[3단계: Transform] transform_batch() → 청킹 + 임베딩 + 해시 생성
  - 10개 문서씩 배치 처리
  - 청킹 → 임베딩 → VectorPayload 생성
  ↓
[4단계: Load] load_batch() → 해시 기반 중복 체크 + Qdrant 저장
  - 5개 벡터씩 배치 처리
  - 해시로 중복 체크
  - unique만 upsert_batch()
```

## guide

### 1. 스크립트 파일 생성

`scripts/{platform}.py` 생성:

```python
from ohra.workers.sync.scripts.base import sync_script

def extract_documents(**config):
    """제너레이터: 문서를 yield"""
    # API 호출하여 문서 가져오기
    for item in api_items:
        yield {
            "id": "...",
            "title": "...",
            "content": "...",
            "url": "...",
            "author": "...",
            "updated_at": datetime(...),
            "source_type": "platform",
            "version_key": "...",  # 변경 감지용 (필수)
            "metadata": {...},  # 플랫폼별 필드
        }

@sync_script(
    source_type="platform",
    chunk_size=1500,
    chunk_overlap=300,
    get_config=lambda s: {"token": s.platform.token},
)
def main(last_sync_time=None, **config):
    return extract_documents(last_sync_time=last_sync_time, **config)
```

### 2. main.py에 추가

- `from ohra.workers.sync.scripts import platform` 추가
- `sync_job()`에 `elif source == "platform"` 추가
- `choices`에 `"platform"` 추가

### 3. 필요시 schemas.py에 필드 추가

```python
# VectorPayload에 플랫폼별 필드 추가
field_name: Optional[str] = None  # platform
```

### 4. transform.py에 필드 할당 (필요시)

```python
field_name=raw_meta.get("field_name") if source_type == "platform" else None,
```

**핵심**: 표준 문서 형식 + `version_key`만 준수하면 나머지는 자동 처리됨
