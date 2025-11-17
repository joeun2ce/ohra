import logging
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime

from dependency_injector.wiring import Provide, inject

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from .connection import SyncDatabase, AsyncDatabase

sqla_version = sa.__version__


@dataclass(init=True, kw_only=True, repr=True)
class AsyncSqlaMixIn(ABC):
    db: AsyncDatabase = field(init=False, repr=False)
    logger: logging.Logger = field(init=False, repr=False)

    @inject
    def __post_init__(self, db: AsyncDatabase = Provide["database.async_db"], name: str | None = None):
        self.db = db
        name = name or self.__class__.__name__
        self.logger = logging.getLogger(name)
        self.logger.info(f"initialized: {name}")


@dataclass(init=True, kw_only=True, repr=True)
class SyncSqlaMixIn(ABC):
    db: SyncDatabase = field(init=False, repr=False)
    logger: logging.Logger = field(init=False, repr=False)

    @inject
    def __post_init__(self, db: SyncDatabase = Provide["database.db"], name: str | None = None):
        self.db = db
        name = name or self.__class__.__name__
        self.logger = logging.getLogger(name)
        self.logger.info(f"initalized: {name}")


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), default=sa.func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        default=sa.func.now(),
        onupdate=sa.func.now(),
    )


class TimestampColumnMixin:
    from sqlalchemy import Column, DateTime, func
    from datetime import datetime

    created_at = Column(DateTime, nullable=False, default=datetime.now, server_default=func.current_timestamp())
    updated_at = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, server_default=func.current_timestamp()
    )
