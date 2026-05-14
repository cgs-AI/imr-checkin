"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.routes import admin, checkin, hosts, visitors, visits

logger = get_logger(__name__)
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    logger.info("imr_checkin.startup", env=get_settings().app_env)
    yield
    logger.info("imr_checkin.shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="IMR Visitor Check-In API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(
        RateLimitExceeded,
        lambda _req, exc: JSONResponse(
            status_code=429,
            content={"detail": "Too many requests"},
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )

    app.include_router(checkin.router)
    app.include_router(visitors.router)
    app.include_router(hosts.router)
    app.include_router(visits.router)
    app.include_router(admin.router)

    @app.get("/healthz", tags=["meta"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
