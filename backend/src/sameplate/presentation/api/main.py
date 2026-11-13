from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from sameplate.infrastructure.config import Settings
from sameplate.infrastructure.db.session import create_db_engine, create_session_factory
from sameplate.presentation.api.health import router as health_router
from sameplate.presentation.api.recipes.router import router as recipes_router


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        # Required fields are loaded from environment variables.
        settings = Settings()  # pyright: ignore[reportCallIssue]

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        engine = create_db_engine(settings)

        try:
            app.state.session_factory = create_session_factory(engine)
            yield
        finally:
            await engine.dispose()

    app = FastAPI(title="sameplate", lifespan=lifespan, debug=settings.debug)
    app.include_router(health_router)
    app.include_router(recipes_router)
    return app
