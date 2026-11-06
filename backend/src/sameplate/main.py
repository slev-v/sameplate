from fastapi import FastAPI

from sameplate.health import router as health_router

app = FastAPI(title="sameplate")

app.include_router(health_router)
