from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import CacheEntry


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def cache_get(session: AsyncSession, key: str) -> dict | list | None:
    row = await session.get(CacheEntry, key)
    if not row:
        return None
    if row.expires_at < _now():
        await session.delete(row)
        await session.flush()
        return None
    return json.loads(row.payload_json)


async def cache_set(session: AsyncSession, key: str, payload: dict | list, ttl_seconds: int) -> None:
    expires = _now() + timedelta(seconds=ttl_seconds)
    row = await session.get(CacheEntry, key)
    raw = json.dumps(payload, ensure_ascii=False)
    if row:
        row.payload_json = raw
        row.expires_at = expires
    else:
        session.add(CacheEntry(key=key, payload_json=raw, expires_at=expires))
    await session.flush()


async def cache_purge_expired(session: AsyncSession) -> int:
    result = await session.execute(delete(CacheEntry).where(CacheEntry.expires_at < _now()))
    return result.rowcount or 0


async def cache_keys_like(session: AsyncSession, prefix: str) -> list[str]:
    result = await session.execute(select(CacheEntry.key).where(CacheEntry.key.like(f"{prefix}%")))
    return list(result.scalars().all())
