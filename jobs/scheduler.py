from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from analytics.prematch import build_prematch_report, format_report
from analytics.value import find_value_bets
from core.config import settings
from core.db import session_scope
from core.models import Subscription, User, UserLeague, ValueAlert
from core.queries import due_prematch_subscriptions
from sports.aggregator import SportsHub

log = logging.getLogger(__name__)


def setup_scheduler(bot: Bot, hub: SportsHub) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    minutes = max(1, settings.scheduler_interval_minutes)
    scheduler.add_job(run_prematch_job, "interval", minutes=minutes, args=[bot, hub], id="prematch")
    scheduler.add_job(run_value_job, "interval", minutes=minutes, args=[bot, hub], id="value")
    return scheduler


async def run_prematch_job(bot: Bot, hub: SportsHub) -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    window_end = now + timedelta(hours=settings.prematch_hours_before)
    async with session_scope() as session:
        items = await due_prematch_subscriptions(session, now, window_end)
        grouped: dict[str, list[Subscription]] = {}
        for sub in items:
            grouped.setdefault(sub.fixture_id, []).append(sub)
        for fixture_id, subs in grouped.items():
            try:
                bundle = await hub.match_bundle(session, fixture_id)
                report = await build_prematch_report(bundle)
                text = format_report(bundle, report)
            except Exception:
                log.exception("prematch failed for %s", fixture_id)
                continue
            for sub in subs:
                try:
                    await bot.send_message(sub.user.telegram_id, text)
                    sub.prematch_sent = True
                except Exception:
                    log.exception("send prematch to %s", sub.user.telegram_id)


async def run_value_job(bot: Bot, hub: SportsHub) -> None:
    async with session_scope() as session:
        result = await session.execute(select(Subscription).order_by(Subscription.kickoff.asc()).limit(20))
        subs = list(result.scalars().all())
        seen: set[str] = set()
        for sub in subs:
            if sub.fixture_id in seen:
                continue
            seen.add(sub.fixture_id)
            try:
                bundle = await hub.match_bundle(session, sub.fixture_id)
                bets = find_value_bets(bundle)
            except Exception:
                log.exception("value job fixture %s", sub.fixture_id)
                continue
            for bet in bets:
                exists = await session.execute(
                    select(ValueAlert).where(
                        ValueAlert.fixture_id == sub.fixture_id,
                        ValueAlert.market == f"{bet.market}:{bet.selection}",
                    )
                )
                if exists.scalar_one_or_none():
                    continue
                session.add(
                    ValueAlert(
                        fixture_id=sub.fixture_id,
                        market=f"{bet.market}:{bet.selection}",
                        edge=bet.edge,
                    )
                )
                users = await session.execute(
                    select(User)
                    .join(UserLeague, UserLeague.user_id == User.id)
                    .where(User.notify_value.is_(True), UserLeague.league_id == sub.league_id)
                    .distinct()
                )
                text = (
                    f"<b>Value alert</b> · {bundle.fixture.title()}\n"
                    f"{bet.as_text()}\n\n"
                    f"<i>Не является рекомендацией ставить.</i>"
                )
                for user in users.scalars().all():
                    try:
                        await bot.send_message(user.telegram_id, text)
                    except Exception:
                        log.exception("value send %s", user.telegram_id)
