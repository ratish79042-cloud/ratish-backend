from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Create async engine with Neon SSL requirements
engine = create_async_engine(
    settings.clean_database_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
    connect_args={"ssl": True}
)

# Async session maker
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for SQLAlchemy declarative models
class Base(DeclarativeBase):
    pass

# FastAPI Dependency for obtaining async db sessions
async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
