from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

log = logging.getLogger(__name__)


class ThrottleMiddleware(BaseMiddleware):
    def __init__(self, rate: float = 0.4) -> None:
        self.rate = rate
        self._last: dict[int, float] = defaultdict(float)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user:
            now = time.monotonic()
            if now - self._last[user.id] < self.rate:
                return None
            self._last[user.id] = now
        return await handler(event, data)


class HubMiddleware(BaseMiddleware):
    def __init__(self, hub) -> None:
        self.hub = hub

    async def __call__(self, handler, event, data):
        data["hub"] = self.hub
        return await handler(event, data)
