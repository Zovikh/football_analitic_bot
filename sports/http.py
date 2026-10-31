from __future__ import annotations

import asyncio
import time

import httpx


class RateLimitedClient:
    def __init__(self, rps: float = 2.0, timeout: float = 20.0) -> None:
        self._min_interval = 1.0 / max(rps, 0.1)
        self._lock = asyncio.Lock()
        self._last = 0.0
        self._client = httpx.AsyncClient(timeout=timeout)

    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        async with self._lock:
            wait = self._min_interval - (time.monotonic() - self._last)
            if wait > 0:
                await asyncio.sleep(wait)
            response = await self._client.request(method, url, **kwargs)
            self._last = time.monotonic()
        response.raise_for_status()
        return response

    async def get_json(self, url: str, **kwargs) -> dict | list:
        response = await self.request("GET", url, **kwargs)
        return response.json()

    async def aclose(self) -> None:
        await self._client.aclose()
