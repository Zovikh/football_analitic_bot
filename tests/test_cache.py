from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from core.cache import cache_get, cache_purge_expired, cache_set
from core.models import Base, CacheEntry


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as item:
        yield item
    await engine.dispose()


async def test_cache_roundtrip(session):
    await cache_set(session, "k", {"a": 1}, ttl_seconds=60)
    assert await cache_get(session, "k") == {"a": 1}


async def test_cache_expired(session):
    await cache_set(session, "old", {"a": 1}, ttl_seconds=1)
    row = await session.get(CacheEntry, "old")
    row.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=5)
    assert await cache_get(session, "old") is None
    assert await cache_purge_expired(session) == 0
