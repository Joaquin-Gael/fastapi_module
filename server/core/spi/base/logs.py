from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from ...models.base import Log
from ...models.enums.base import LogType, LogLevel, LogStatus, LogAction

class SPILogs:
    def __init__(self, log_class: Log = Log):
        self.log_class = log_class

    async def get_log_by_id(self, log_id: int, session: AsyncSession):
        try:
            statement = select(self.log_class).where(
                getattr(self.log_class, "id") == log_id
            )
            result = await session.execute(statement)
            return result.scalars().first()
        except Exception as e:
            raise e

    async def get_logs(self, session: AsyncSession, offset: int = 0, limit: int = 100, word_key: str | None = None):
        try:
            if word_key:
                statement = select(self.log_class).where(
                    getattr(self.log_class, "final_message").like(f"%{word_key}%")
                ).offset(offset).limit(limit)
            else:
                statement = select(self.log_class).offset(offset).limit(limit)
            print(f"{statement}")
            result = await session.execute(statement)
            return result.scalars().all()
        except Exception as e:
            raise e

    async def get_logs_by_type(self, log_type: LogType, session: AsyncSession):
        try:
            statement = select(self.log_class).where(
                getattr(self.log_class, "type") == log_type
            )
            result = await session.execute(statement)
            return result.scalars().all()
        except Exception as e:
            raise e

    async def get_logs_by_level(self, log_level: LogLevel, session: AsyncSession):
        try:
            statement = select(self.log_class).where(
                getattr(self.log_class, "level") == log_level
            )
            result = await session.execute(statement)
            return result.scalars().all()
        except Exception as e:
            raise e

    async def get_logs_by_status(self, log_status: LogStatus, session: AsyncSession):
        try:
            statement = select(self.log_class).where(
                getattr(self.log_class, "status") == log_status
            )
            result = await session.execute(statement)
            return result.scalars().all()
        except Exception as e:
            raise e

    async def get_logs_by_action(self, log_action: LogAction, session: AsyncSession):
        try:
            statement = select(self.log_class).where(
                getattr(self.log_class, "action") == log_action
            )
            result = await session.execute(statement)
            return result.scalars().all()
        except Exception as e:
            raise e
