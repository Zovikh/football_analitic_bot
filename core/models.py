from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bankroll: Mapped[float] = mapped_column(Float, default=0.0)
    notify_value: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    leagues: Mapped[list["UserLeague"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserLeague(Base):
    __tablename__ = "user_leagues"
    __table_args__ = (UniqueConstraint("user_id", "league_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    league_id: Mapped[str] = mapped_column(String(32), index=True)
    league_name: Mapped[str] = mapped_column(String(128))

    user: Mapped[User] = relationship(back_populates="leagues")


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (UniqueConstraint("user_id", "fixture_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    fixture_id: Mapped[str] = mapped_column(String(64), index=True)
    home_team: Mapped[str] = mapped_column(String(128))
    away_team: Mapped[str] = mapped_column(String(128))
    league_id: Mapped[str] = mapped_column(String(32))
    kickoff: Mapped[datetime] = mapped_column(DateTime, index=True)
    status: Mapped[str] = mapped_column(String(32), default="NS")
    prematch_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship(back_populates="subscriptions")


class CacheEntry(Base):
    __tablename__ = "cache_entries"

    key: Mapped[str] = mapped_column(String(256), primary_key=True)
    payload_json: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)


class HrSession(Base):
    __tablename__ = "hr_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    candidate_name: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="in_progress")
    score: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    answers: Mapped[list["HrAnswer"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class HrAnswer(Base):
    __tablename__ = "hr_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("hr_sessions.id", ondelete="CASCADE"))
    question_key: Mapped[str] = mapped_column(String(64))
    answer_text: Mapped[str] = mapped_column(Text)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    comment: Mapped[str] = mapped_column(Text, default="")

    session: Mapped[HrSession] = relationship(back_populates="answers")


class ValueAlert(Base):
    __tablename__ = "value_alerts"
    __table_args__ = (UniqueConstraint("fixture_id", "market"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fixture_id: Mapped[str] = mapped_column(String(64), index=True)
    market: Mapped[str] = mapped_column(String(64))
    edge: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
