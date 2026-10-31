import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from core.models import Base, User, UserLeague
from core.queries import users_apl_bankroll_over


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as item:
        yield item
    await engine.dispose()


async def test_join_apl_bankroll(session):
    vip = User(telegram_id=1, bankroll=2500)
    poor = User(telegram_id=2, bankroll=100)
    other = User(telegram_id=3, bankroll=5000)
    session.add_all([vip, poor, other])
    await session.flush()
    session.add_all(
        [
            UserLeague(user_id=vip.id, league_id="PL", league_name="АПЛ"),
            UserLeague(user_id=poor.id, league_id="PL", league_name="АПЛ"),
            UserLeague(user_id=other.id, league_id="RL", league_name="РПЛ"),
        ]
    )
    await session.flush()
    found = await users_apl_bankroll_over(session, 1000)
    assert [u.telegram_id for u in found] == [1]
