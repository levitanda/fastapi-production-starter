from collections.abc import AsyncGenerator
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

_engine: Optional[AsyncEngine] = None
_AsyncSessionLocal: Optional[async_sessionmaker] = None


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        url = settings.DATABASE_URL
        kwargs: dict = {"echo": settings.DEBUG}
        if not _is_sqlite(url):
            kwargs["pool_pre_ping"] = True
            kwargs["pool_size"] = 10
            kwargs["max_overflow"] = 20
        _engine = create_async_engine(url, **kwargs)
    return _engine


def get_session_factory() -> async_sessionmaker:
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _AsyncSessionLocal


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
