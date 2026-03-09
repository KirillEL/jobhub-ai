from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from parser_api.core.config import get_settings

settings = get_settings()

engine: AsyncEngine = create_async_engine(settings.postgres_dsn, pool_pre_ping=True, echo=False)
SessionLocal: AsyncSession = async_sessionmaker[AsyncSession](
    bind=engine, class_=AsyncSession, autoflush=False, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    db = SessionLocal()
    try:
            yield db
    finally:
        await db.close()
