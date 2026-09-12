from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings

engine = create_async_engine(settings.database_url, echo=(settings.environment == "development"))

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """
    FastAPI dependency — yields a DB session per request, closes it after.
    Usage in a router: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        yield session
