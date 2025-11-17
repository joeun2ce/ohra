from pydantic import BaseModel, Field


class DatabaseSettings(BaseModel):
    url: str = Field(default="sqlite+aiosqlite:///data/database.db")
    init: bool = False
    echo: bool = True
    pool_size: int = 10
    max_overflow: int = 2
    pool_recycle: int = 3600
    pg_schema: str = "public"
    pool_timeout: int = 30
    pool_pre_ping: bool = True
