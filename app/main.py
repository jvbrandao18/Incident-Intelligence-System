from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.database import init_db
from app.routers import health, incidents, metrics


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    init_db()
    yield


app = FastAPI(
    title="Incident Intelligence System",
    description="Rule-based incident classification, root cause hints and historical similarity search.",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(health.router)
app.include_router(incidents.router)
app.include_router(metrics.router)
