from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from sameplate.core.config import Settings
from sameplate.core.dependencies import get_session
from sameplate.infrastructure.db.session import create_db_engine
from sameplate.main import create_app


@pytest.fixture
def test_settings() -> Settings:
    settings = Settings()  # pyright: ignore[reportCallIssue]

    if settings.postgres_host != "db-test" or settings.postgres_db != "sameplate_test":
        raise RuntimeError("Run these tests through Compose")

    return settings


@pytest_asyncio.fixture
async def db_session(test_settings: Settings) -> AsyncIterator[AsyncSession]:
    engine = create_db_engine(test_settings)

    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()

            try:
                async with AsyncSession(
                    bind=connection,
                    expire_on_commit=False,
                    join_transaction_mode="create_savepoint",
                ) as session:
                    yield session
            finally:
                await transaction.rollback()
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def client(
    test_settings: Settings, db_session: AsyncSession
) -> AsyncIterator[AsyncClient]:
    app = create_app(test_settings)

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    try:
        transport = ASGITransport(app=app)

        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as http_client:
            yield http_client
    finally:
        app.dependency_overrides.clear()
