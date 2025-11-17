from typing import Optional
from pydantic import BaseModel


class VectorPayload(BaseModel):
    source_document_id: str
    content: str
    chunk_index: int
    source_type: str
    title: str
    url: Optional[str] = None
    author: Optional[str] = None
    last_modified_at: Optional[str] = None
    hash: str
    version_key: Optional[str] = None

    # platform specific fields
    page_id: Optional[str] = None  # Confluence
    space_key: Optional[str] = None  # Confluence
    issue_key: Optional[str] = None  # Jira
    project_key: Optional[str] = None  # Jira

    model_config = {"extra": "ignore"}
