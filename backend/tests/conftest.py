"""
CivilInc Test Configuration
Session-scoped engine with function-scoped transactions for test isolation.
"""
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import JSON, event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool


# ─── Patch Base.metadata once at module load ────────────────────────────────
def _patch_metadata():
    """Replace JSONB→JSON and clear indexes for SQLite compatibility."""
    from sqlalchemy.dialects.postgresql import JSONB
    from app.db.base import Base
    import app.models  # ensure all models are registered

    for table in Base.metadata.tables.values():
        for col in table.columns:
            if isinstance(col.type, JSONB):
                col.type = JSON()
        table.indexes.clear()

_patch_metadata()


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_engine():
    """Single in-memory SQLite engine shared across the whole test session."""
    return create_async_engine(
        "sqlite+aiosqlite:///file:testdb?mode=memory&cache=shared&uri=true",
        connect_args={"check_same_thread": False},
        echo=False,
    )


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables(test_engine):
    """Create all tables once for the session."""
    from app.db.base import Base
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine):
    """Function-scoped session with rollback for test isolation."""
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    from app.main import app
    from app.db.base import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_commissioner(db_session):
    from app.models.user import User
    from app.core.permissions import Role
    from app.core.security import security
    import uuid
    user = User(
        id=uuid.uuid4(),
        email=f"comm_{uuid.uuid4().hex[:8]}@test.com",
        full_name="Test Commissioner",
        hashed_password=security.hash_password("Admin@1"),
        role=Role.COMMISSIONER,
        is_active=True, is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def test_citizen(db_session):
    from app.models.user import User
    from app.core.permissions import Role
    from app.core.security import security
    import uuid
    user = User(
        id=uuid.uuid4(),
        email=f"cit_{uuid.uuid4().hex[:8]}@test.com",
        full_name="Test Citizen",
        hashed_password=security.hash_password("Citizen@1"),
        role=Role.CITIZEN,
        is_active=True, is_verified=True,
        ward_number="Ward-1",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def commissioner_token(test_commissioner):
    from app.core.security import security
    return security.create_access_token(
        subject=test_commissioner.id, role=test_commissioner.role.value)


@pytest_asyncio.fixture
async def citizen_token(test_citizen):
    from app.core.security import security
    return security.create_access_token(
        subject=test_citizen.id, role=test_citizen.role.value)
