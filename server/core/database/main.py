from sqlmodel import SQLModel
from fastapi import Depends
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from server.core.config import CoreSettings as Settings


engine: AsyncEngine = create_async_engine(Settings().database_url, echo=Settings().debug)

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
