import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Generator, Set, Tuple
from atlassian import Confluence
from bs4 import BeautifulSoup

from ohra.workers.sync.scripts.base import sync_script

logger = logging.getLogger(__name__)


def _fetch_page(
    confluence: Confluence,
    page_id: str,
) -> Optional[dict]:
    """
    get_page_by_id를 expand 포함해서 안정적으로 호출하는 함수
    """
    return confluence.get_page_by_id(
        page_id,
        expand=(
            "body.storage,"
            "version,"
            "metadata,"
            "children.page,"
            "children.page.children,"
            "children.page.children.children"
        )
    )


def _get_all_children(
    confluence: Confluence,
    page_id: str,
) -> list:
    """
    페이지의 모든 children을 pagination 처리하여 가져오기
    """
    all_children = []
    start = 0
    limit = 100
    
    while True:
        try:
            children = confluence.get_page_child_by_type(
                page_id, type="page", start=start, limit=limit
            )
            
            if isinstance(children, dict):
                child_list = children.get("results", [])
                size = children.get("size", len(child_list))
            else:
                child_list = children if isinstance(children, list) else []
                size = len(child_list)
            
            all_children.extend(child_list)
            
            if size < limit or len(child_list) == 0:
                break
            
            start += limit
        except Exception as e:
            logger.error(f"Failed to fetch children for page {page_id} at start={start}: {e}")
            break
    
    return all_children


def _get_page_with_children(
    confluence: Confluence,
    page_id: str,
    space_key: str,
    base_url: str,
    last_sync_time: Optional[datetime],
    visited: Set[Tuple[str, str]],
) -> Generator[Dict[str, Any], None, None]:
    """
    Recursively get page and all its children.
    visited는 (page_id, version) 튜플로 관리하여 버전 변경 감지.
    """
    try:
        page = _fetch_page(confluence, page_id)
        if not page:
            return

        version_num = str(page.get("version", {}).get("number", ""))
        visit_key = (page_id, version_num)
        
        # 이미 동일 버전을 방문했다면 skip
        if visit_key in visited:
            return
        visited.add(visit_key)

        should_yield = True
        if last_sync_time:
            version_when = page.get("version", {}).get("when", "")
            if version_when:
                page_updated = datetime.fromisoformat(version_when.replace("Z", "+00:00"))
                if page_updated < last_sync_time:
                    should_yield = False

        page_title = page.get("title", "")
        print(f"[PAGE] ID: {page_id}, Title: {page_title}")
        
        if should_yield:
            doc = _build_document(page, space_key, base_url)
            if doc:
                print(f"[YIELD] Document: {doc.get('title')}, Author: {doc.get('author')}, ID: {doc.get('id')}")
                yield doc

        # 하위 페이지는 메인 페이지가 스킵되어도 확인해야 함
        # expand로 가져온 children이 있으면 우선 사용, 없으면 API 호출
        child_container = (
            page.get("children", {})
            .get("page", {})
            .get("results", [])
        )
        
        # expand로 가져온 children이 없거나 부족하면 API로 전체 가져오기
        if not child_container:
            child_container = _get_all_children(confluence, page_id)
        
        print(f"[CHILDREN] Found {len(child_container)} children for page {page_id} ({page_title})")
        for child in child_container:
            child_id = child.get("id")
            child_title = child.get("title", "Unknown")
            print(f"[SUB-PAGE] ID: {child_id}, Title: {child_title}")
            if child_id:
                yield from _get_page_with_children(
                    confluence, child_id, space_key, base_url, last_sync_time, visited
                )
    except Exception as e:
        logger.error(f"Failed to fetch page {page_id}: {e}", exc_info=True)


def extract_documents(url: str, email: str, token: str, last_sync_time: Optional[datetime] = None):
    """
    Confluence에서 문서를 가져오는 제너레이터 (하위 페이지 포함)

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

    # 모든 스페이스 타입을 pagination으로 가져오기
    all_spaces = []
    start = 0
    limit = 500
    
    while True:
        try:
            # space_type을 지정하지 않으면 모든 타입 가져오기
            spaces_response = confluence.get_all_spaces(start=start, limit=limit)
            
            if isinstance(spaces_response, dict):
                space_list = spaces_response.get("results", [])
                size = spaces_response.get("size", len(space_list))
            else:
                space_list = spaces_response if isinstance(spaces_response, list) else []
                size = len(space_list)
            
            all_spaces.extend(space_list)
            
            if size < limit or len(space_list) == 0:
                break
            
            start += limit
        except Exception as e:
            logger.error(f"Failed to fetch spaces at start={start}: {e}")
            break
    
    spaces = [s.get("key") for s in all_spaces if s.get("key")]
    print(f"[TOTAL] Found {len(spaces)} spaces")

    for space_key in spaces:
        print(f"\n[SPACE] {space_key}")
        visited: Set[Tuple[str, str]] = set()
        
        try:
            # Space의 homepage 가져오기
            space_data = confluence.get_space(space_key, expand="homepage")
            home_page = space_data.get("homepage")
            
            if not home_page:
                print(f"[WARN] No homepage for space {space_key}, skipping")
                continue
            
            home_id = home_page.get("id")
            if not home_id:
                print(f"[WARN] Homepage has no ID for space {space_key}, skipping")
                continue
            
            print(f"[ROOT] homepage id={home_id}")
            
            # homepage부터 재귀적으로 모든 하위 페이지 탐색
            yield from _get_page_with_children(
                confluence, home_id, space_key, url, last_sync_time, visited
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch from space {space_key}: {e}", exc_info=True)
            continue


def _build_document(page: Dict[str, Any], space_key: str, base_url: str) -> Optional[Dict[str, Any]]:
    try:
        body = page.get("body", {}).get("storage", {}).get("value", "")
        soup = BeautifulSoup(body, "html.parser")
        content = soup.get_text(separator="\n", strip=True)

        if not content or len(content.strip()) < 50:
            return None

        version = page.get("version", {})
        webui_link = page.get("_links", {}).get("webui", "")
        if webui_link:
            if webui_link.startswith("/spaces/"):
                webui_link = f"/wiki{webui_link}"
            base_url_http = base_url.replace("https://", "http://")
            url = f"{base_url_http.rstrip('/')}{webui_link}"
        else:
            url = None
        version_number = version.get("number")
        version_by = version.get("by", {})
        author = version_by.get("displayName", "") or version_by.get("username", "") or version_by.get("userKey", "")
        
        print(f"[BUILD] Page ID: {page.get('id')}, Title: {page.get('title')}, Author: {author}")
        print(f"[BUILD] Version by object: {version_by}")

        return {
            "id": page.get("id", ""),
            "title": page.get("title", ""),
            "content": content,
            "url": url,
            "author": author,
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
