import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Generator, Set, Tuple
from atlassian import Confluence
from bs4 import BeautifulSoup

from ohra.workers.sync.scripts.base import sync_script


def _fetch_page(confluence: Confluence, page_id: str) -> Optional[dict]:
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


def _get_all_children(confluence: Confluence, page_id: str) -> list:
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
        except Exception:
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
    try:
        page = _fetch_page(confluence, page_id)
        if not page:
            return

        version_num = str(page.get("version", {}).get("number", ""))
        visit_key = (page_id, version_num)
        
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
        
        if should_yield:
            doc = _build_document(page, space_key, base_url)
            if doc:
                yield doc

        child_container = (
            page.get("children", {})
            .get("page", {})
            .get("results", [])
        )
        
        if not child_container:
            child_container = _get_all_children(confluence, page_id)
        
        for child in child_container:
            child_id = child.get("id")
            if child_id:
                yield from _get_page_with_children(
                    confluence, child_id, space_key, base_url, last_sync_time, visited
                )
    except Exception:
        pass


def extract_documents(url: str, email: str, token: str, last_sync_time: Optional[datetime] = None):
    confluence = Confluence(url=url, username=email, password=token)

    all_spaces = []
    start = 0
    limit = 500

    while True:
        try:
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
        except Exception:
            break

    spaces = [s.get("key") for s in all_spaces if s.get("key")]

    for space_key in spaces:
        visited: Set[Tuple[str, str]] = set()
        
        try:
            space_data = confluence.get_space(space_key, expand="homepage")
            home_page = space_data.get("homepage")
            
            if not home_page:
                continue

            home_id = home_page.get("id")
            if not home_id:
                continue
            
            yield from _get_page_with_children(
                confluence, home_id, space_key, url, last_sync_time, visited
            )

        except Exception:
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
    except Exception:
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
    return extract_documents(last_sync_time=last_sync_time, **config)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
