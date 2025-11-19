import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from jira import JIRA

from ohra.workers.sync.scripts.base import sync_script


def extract_documents(url: str, email: str, token: str, last_sync_time: Optional[datetime] = None):
    """
    Jira에서 이슈를 가져오는 제너레이터

    Args:
        url: Jira base URL
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
            "source_type": "jira",
            "metadata": {"issue_key": str, "project_key": str}
        }
    """
    jira = JIRA(server=url, basic_auth=(email, token), validate=False)

    if last_sync_time:
        since_str = last_sync_time.strftime("%Y-%m-%d %H:%M")
        jql = f'updated >= "{since_str}" ORDER BY updated DESC'
    else:
        jql = "updated >= -180d ORDER BY updated DESC"

    max_results = 100
    next_page_token = None

    while True:
        try:
            issues = jira.enhanced_search_issues(
                jql_str=jql,
                nextPageToken=next_page_token,
                maxResults=max_results,
                fields=[
                    "summary",
                    "description",
                    "issuetype",
                    "status",
                    "priority",
                    "assignee",
                    "reporter",
                    "created",
                    "updated",
                    "project",
                    "comment",
                ],
                expand=["renderedFields"],
            )

            if not issues:
                break

            for issue in issues:
                doc = _build_document(issue, url)
                if doc:
                    yield doc

            if hasattr(issues, 'nextPageToken') and issues.nextPageToken:
                next_page_token = issues.nextPageToken
            else:
                break

        except Exception:
            break


def _build_document(issue, base_url: str) -> Optional[Dict[str, Any]]:
    try:
        fields = issue.fields

        description = getattr(fields, "description", None) or ""
        summary = getattr(fields, "summary", "Untitled")

        content_parts = [summary]
        if description:
            content_parts.append(description)

        if hasattr(fields, "comment") and fields.comment:
            for comment in fields.comment.comments:
                content_parts.append(f"Comment: {comment.body}")

        content = "\n\n".join(content_parts)

        if not content or len(content.strip()) < 50:
            return None

        project_key = fields.project.key if fields.project else None
        url = f"{base_url.rstrip('/')}/browse/{issue.key}" if issue.key else None
        updated_at = (
            datetime.fromisoformat(fields.updated.replace("Z", "+00:00")) if hasattr(fields, "updated") else None
        )

        return {
            "id": str(issue.id),
            "title": summary,
            "content": content,
            "url": url,
            "author": getattr(fields.reporter, "displayName", "") if fields.reporter else "",
            "updated_at": updated_at,
            "source_type": "jira",
            "version_key": updated_at.isoformat() if updated_at else None,
            "metadata": {"issue_key": issue.key, "project_key": project_key},
        }
    except Exception:
        return None


@sync_script(
    source_type="jira",
    chunk_size=800,
    chunk_overlap=150,
    get_config=lambda s: {
        "url": s.atlassian.base_url.rstrip("/"),
        "email": s.atlassian.email,
        "token": s.atlassian.token,
    },
)
def main(last_sync_time: Optional[datetime] = None, **config):
    return extract_documents(last_sync_time=last_sync_time, **config)


if __name__ == "__main__":
    asyncio.run(main())
