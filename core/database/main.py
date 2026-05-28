import traceback

from sqlmodel import SQLModel
from fastapi import Depends
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from core.config import settings
from core.utils.logger import get_logger, _get_celery_logger

logger = get_logger(__name__)
stealth_logger = _get_celery_logger(__name__)

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False, #Settings().debug,
    pool_size=10,
    max_overflow=20,
    connect_args={
        "ssl":None,
        #"server_settings":{
        #    "channel_binding":"require"
        #}
    }
)

async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
    except Exception as e:
        stealth_logger.error(e)
        stealth_logger.error(traceback.format_exc())


async def get_session() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session

async def close_db():
    await engine.dispose()

SessionDep = Annotated[AsyncSession, Depends(get_session)]
METADATA = SQLModel.metadata
DATABASE_URL = settings.database_url
