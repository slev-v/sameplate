import pytest
from httpx import ASGITransport, AsyncClient

from sameplate.core.config import Settings
from sameplate.main import create_app


@pytest.mark.asyncio
async def test_lifespan_and_real_session_dependency(test_settings: Settings):
    app = create_app(test_settings)

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/recipes", params={"limit": 1})

        assert response.status_code == 200
        assert isinstance(response.json(), list)
