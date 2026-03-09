from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from parser_api.api.router import api_router
from parser_api.core.config import get_settings
from parser_api.db import models  # noqa: F401
from parser_api.db.base import Base
from parser_api.db.session import engine
from parser_api.integrations.parser_client import close_parser_http_client
from parser_api.services.daily_check_scheduler import DailyCheckScheduler


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        scheduler = DailyCheckScheduler(settings=settings)
        if settings.create_schema_on_start:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        scheduler.start()
        yield
        scheduler.shutdown()
        await close_parser_http_client()

    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def root() -> dict[str, str]:
        return {"message": "Parser API is running"}

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
