from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.models import Subscription, User, UserLeague


async def get_or_create_user(session: AsyncSession, telegram_id: int, username: str | None) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user:
        if username and user.username != username:
            user.username = username
        return user
    user = User(telegram_id=telegram_id, username=username)
    session.add(user)
    await session.flush()
    return user


async def users_apl_bankroll_over(session: AsyncSession, min_bankroll: float = 1000.0) -> list[User]:
    """Пользователи, которые следят за АПЛ и имеют банкролл > порога."""
    stmt = (
        select(User)
        .join(UserLeague, UserLeague.user_id == User.id)
        .where(UserLeague.league_id == "PL", User.bankroll > min_bankroll)
        .options(selectinload(User.leagues))
        .distinct()
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def users_for_value_alerts(session: AsyncSession, league_id: str | None = None) -> list[User]:
    stmt = select(User).where(User.notify_value.is_(True)).options(selectinload(User.leagues))
    if league_id:
        stmt = stmt.join(UserLeague).where(UserLeague.league_id == league_id).distinct()
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def due_prematch_subscriptions(session: AsyncSession, start: object, end: object) -> list[Subscription]:
    stmt = (
        select(Subscription)
        .where(
            Subscription.prematch_sent.is_(False),
            Subscription.kickoff >= start,
            Subscription.kickoff <= end,
        )
        .options(selectinload(Subscription.user))
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
