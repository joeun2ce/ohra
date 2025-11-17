import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from atlassian import Confluence
from bs4 import BeautifulSoup

from ohra.workers.sync.scripts.base import sync_script

logger = logging.getLogger(__name__)


def extract_documents(url: str, email: str, token: str, last_sync_time: Optional[datetime] = None):
    """
    Confluence에서 문서를 가져오는 제너레이터

    Args:
        url: Confluence base URL
        email: Atlassian 이메일
        token: API 토큰
        last_sync_time: 마지막 동기화 시간

    Yields:
        Dict[str, Any]: 표준 문서 형식
        {
            "id": str,
            "title": str,
            "content": str,
            "url": Optional[str],
            "author": str,
            "updated_at": Optional[datetime],
            "source_type": "confluence",
            "metadata": {"page_id": str, "space_key": str}
        }
    """
    confluence = Confluence(url=url, username=email, password=token)

    spaces_response = confluence.get_all_spaces(start=0, limit=500, space_type="global")
    spaces = [s.get("key") for s in spaces_response.get("results", []) if s.get("key")]

    for space_key in spaces:
        start = 0
        limit = 100

        while True:
            try:
                pages = confluence.get_all_pages_from_space(
                    space=space_key, start=start, limit=limit, status="current", expand="body.storage,version,metadata"
                )

                if not pages:
                    break

                if isinstance(pages, dict):
                    page_list = pages.get("results", [])
                    size = pages.get("size", len(page_list))
                else:
                    page_list = pages if isinstance(pages, list) else []
                    size = len(page_list)

                if not page_list:
                    break

                for page in page_list:
                    if last_sync_time:
                        version_when = page.get("version", {}).get("when", "")
                        if version_when:
                            page_updated = datetime.fromisoformat(version_when.replace("Z", "+00:00"))
                            if page_updated < last_sync_time:
                                continue

                    doc = _build_document(page, space_key, url)
                    if doc:
                        yield doc

                if size < limit:
                    break

                start += limit
                del pages

            except Exception as e:
                logger.error(f"Failed to fetch from space {space_key}: {e}", exc_info=True)
                break


def _build_document(page: Dict[str, Any], space_key: str, base_url: str) -> Optional[Dict[str, Any]]:
    try:
        body = page.get("body", {}).get("storage", {}).get("value", "")
        soup = BeautifulSoup(body, "html.parser")
        content = soup.get_text(separator="\n", strip=True)

        if not content or len(content.strip()) < 50:
            return None

        version = page.get("version", {})
        webui_link = page.get("_links", {}).get("webui", "")
        url = f"{base_url.rstrip('/')}{webui_link}" if webui_link else None
        version_number = version.get("number")

        return {
            "id": page.get("id", ""),
            "title": page.get("title", ""),
            "content": content,
            "url": url,
            "author": version.get("by", {}).get("displayName", ""),
            "updated_at": datetime.fromisoformat(version.get("when", "").replace("Z", "+00:00"))
            if version.get("when")
            else None,
            "source_type": "confluence",
            "version_key": str(version_number) if version_number else None,
            "metadata": {"page_id": page.get("id"), "space_key": space_key, "version": version_number},
        }
    except Exception as e:
        logger.error(f"Failed to build document from page {page.get('id')}: {e}", exc_info=True)
        return None


@sync_script(
    source_type="confluence",
    chunk_size=1500,
    chunk_overlap=300,
    get_config=lambda s: {
        "url": s.atlassian.base_url.rstrip("/"),
        "email": s.atlassian.email,
        "token": s.atlassian.token,
    },
)
def main(last_sync_time: Optional[datetime] = None, **config):
    """
    Confluence 동기화 메인 함수

    데코레이터가 자동으로:
    - extract_documents 호출
    - 중복 체크
    - 청킹 + 임베딩 + 벡터 저장
    """
    return extract_documents(last_sync_time=last_sync_time, **config)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
