from sqlmodel import SQLModel, Field, select
from sqlalchemy.dialects.postgresql import UUID as PSUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declared_attr, mapped_column, Mapped
from sqlalchemy import event
from uuid import UUID, uuid5
from typing import Any

#from server.core.database import get_session
from server.core.utils.logger import get_logger

logger = get_logger(__name__)

class MixinBaseSQLModel:
    @declared_attr
    def id(cls) -> Mapped[UUID]:
        id_name = [ch.lower() if idx == 0 else f"_{ch.lower()}" for idx, ch in enumerate(str(cls.__name__)) if ch.isupper() and idx > 0]
        return mapped_column(PSUUID, default_factory=uuid5, primary_key=True, name=f"{id_name}_id")
        


class BaseSQLModel(SQLModel, MixinBaseSQLModel, table=False):
    id: UUID = Field(
        sa_type=PSUUID,
        default_factory=uuid5,
        primary_key=True,
        sa_column_kwargs={"name": "id"}
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"name": "created_at"}
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"name": "updated_at"}
    )

    @classmethod
    async def get_by_id(cls, id: UUID, session: AsyncSession) -> cls | None:
        try:
            result = await session.get(cls, id)
            return result
        except Exception as e:
            logger.debug(f"Error al obtener {cls.__name__} por id {id}: {e}")
            raise e

    @classmethod
    async def get(cls, form: dict, session: AsyncSession) -> list[cls]:
        try:
            query = select(cls)
            fields: dict = form.pop("fields")
            limit = form["limit"]
            offset = form.get("offset", 0)
            page = form.get("page", 0)
            for key, value in fields.items():
                if value is not None:
                    query = query.where(getattr(cls, key) == value)
            
            if not offset:
                query.offset(page * limit).limit(limit)
            else:
                query.offset(offset).limit(limit)
            
            query.order_by(cls.id)

            results = await session.execute(query)
            return results.fetchall()
        except Exception as e:
            logger.debug(f"Error al obtener {cls.__name__} por {form}: {e}")
            raise e
    @classmethod
    async def create(cls, data: dict, session: AsyncSession):
        try:
            instance = cls(**data)
            session.add(instance)
            await session.commit()
            return instance
        except Exception as e:
            logger.debug(f"Error al crear {cls.__name__} por {data}: {e}")
            raise e

    async def delete(self, session: AsyncSession):
        try:
            await session.delete(self)
            await session.commit()
        except Exception as e:
            logger.debug(f"Error al eliminar {self.__class__.__name__} por id {self.id}: {e}")
            raise e
    
    @classmethod
    async def delete_by(cls, field: str, value: Any, session: AsyncSession):
        try:
            query = select(cls).where(getattr(cls, field) == value)
            result = await session.execute(query)
            values = result.fetchall()
            if values:
                for v in values:
                    await session.delete(v)
                await session.commit()
            else:
                logger.info(f"No se encontraron {cls.__name__} con {field} {value}")
        except Exception as e:
            logger.debug(f"Error al eliminar {cls.__name__} por {field} {value}: {e}")
            raise e

@event.listens_for(BaseSQLModel, "before_insert")
def before_insert(mapper, connection, target):
    target.created_at = datetime.now()
    target.updated_at = datetime.now()

@event.listens_for(BaseSQLModel, "before_update")
def before_update(mapper, connection, target):
    target.updated_at = datetime.now()