from sqlmodel import SQLModel
from fastapi import Depends
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from server.core.config import CoreSettings as Settings
from server.core.utils.logger import get_logger

logger = get_logger(__name__)

engine: AsyncEngine = create_async_engine(
    Settings().database_url.split("?")[0], 
    echo=False, #Settings().debug,
    pool_size=10,
    max_overflow=20,
    connect_args={
        "ssl":"require",
        "server_settings":{
            "channel_binding":"require"
        }
    }
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session

async def close_db():
    await engine.dispose()

SessionDep = Annotated[AsyncSession, Depends(get_session)]
METADATA = SQLModel.metadata
DATABASE_URL = Settings().database_url
