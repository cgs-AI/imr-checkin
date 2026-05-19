"""Fixtures for HubSpot service tests."""

from datetime import datetime
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app import models  # noqa: F401
from app.models.host import Host
from app.models.visit import Visit
from app.models.visitor import Visitor


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with eng.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture
async def session(session_factory):
    async with session_factory() as s:
        yield s


@pytest_asyncio.fixture
async def make_visitor(session):
    async def _make(email: str | None = "visitor@example.com", full_name: str = "Test Visitor") -> Visitor:
        now = datetime.utcnow()
        visitor = Visitor(
            id=uuid4(),
            full_name=full_name,
            email=email,
            phone="+353871234567",
            company="Test Co",
            job_title="Tester",
            created_at=now,
            updated_at=now,
        )
        session.add(visitor)
        await session.commit()
        await session.refresh(visitor)
        return visitor

    return _make


@pytest_asyncio.fixture
async def make_host(session):
    async def _make() -> Host:
        host = Host(
            id=uuid4(),
            display_name="Jane Host",
            email="jane@imr.ie",
            account_enabled=True,
        )
        session.add(host)
        await session.commit()
        await session.refresh(host)
        return host

    return _make


@pytest_asyncio.fixture
async def make_visit(session):
    async def _make(visitor: Visitor, host: Host | None = None) -> Visit:
        now = datetime.utcnow()
        visit = Visit(
            id=uuid4(),
            visitor_id=visitor.id,
            host_id=host.id if host else None,
            arrived_at=now,
            source="qr_self_checkin",
            created_at=now,
        )
        session.add(visit)
        await session.commit()
        await session.refresh(visit)
        return visit

    return _make
