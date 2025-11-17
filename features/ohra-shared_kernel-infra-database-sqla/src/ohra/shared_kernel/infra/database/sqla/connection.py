import logging
from dataclasses import dataclass, field
from typing import Union, TYPE_CHECKING, AsyncGenerator
from contextlib import contextmanager, asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)

from sqlalchemy.orm import Session, sessionmaker, scoped_session
from sqlalchemy import create_engine, Engine


from typing_extensions import Annotated

if TYPE_CHECKING:
    from .settings import DatabaseSettings

logger = logging.getLogger("ohra.database.sqla")
AsyncSessions = Annotated[Union[AsyncSession, async_scoped_session], "SQLA AsyncSession"]
Sessions = Annotated[Union[Session, scoped_session], "SQLA Session"]


@dataclass(init=True, kw_only=True, slots=True)
class SyncDatabase:
    engine: Engine = field(init=False, repr=False)
    session_factory: sessionmaker = field(init=False, repr=False)
    settings: "DatabaseSettings" = field(init=True, repr=False)

    def __post_init__(self) -> None:
        url = self.settings.url
        echo = self.settings.echo

        engine = create_engine(url, echo=echo)
        self.engine = engine
        self.session_factory = sessionmaker(bind=engine, expire_on_commit=False, autocommit=False, autoflush=False)

    @contextmanager
    def session(self) -> Sessions:
        session: Sessions = self.session_factory()

        try:
            yield session
        except Exception as e:
            session.rollback()
            raise e
        finally:
            if isinstance(session, Session):
                session.close()
            elif isinstance(session, scoped_session):
                session.remove()
        logger.info(f"pool: {self.engine.pool.status()}")


@dataclass(init=True, kw_only=True, slots=True)
class AsyncDatabase:
    engine: AsyncEngine = field(init=False, repr=False)
    session_factory: async_sessionmaker[AsyncSession] = field(init=False, repr=False)
    settings: "DatabaseSettings" = field(init=True, repr=False)

    def __post_init__(self) -> None:
        url = self.settings.url
        echo = self.settings.echo

        self.engine = create_async_engine(
            url,
            echo=echo,
            pool_pre_ping=True,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info(f"AsyncDatabase initialized with URL: {url}")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
