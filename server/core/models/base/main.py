from sqlmodel import SQLModel, Field, select
from sqlalchemy.dialects.postgresql import UUID as PSUUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declared_attr, mapped_column, Mapped
from sqlalchemy import event
from uuid import UUID, uuid5

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

    async def get_by_id(self, id: UUID, session: AsyncSession) -> self:
        try:
            query = select(self).where(self.id == id)
            result = await session.exec(query)
            return result.first()
        except Exception as e:
            logger.error(f"Error al obtener {self.__name__} por id {id}: {e}")
            raise e

    async def get(self, form: dict, session: AsyncSession) -> list[self]:
        try:
            query = select(self)
            fields = form.popitem("fields")
            limit = form["limit"]
            offset = form.get("offset", 0)
            page = form.get("page", 0)
            for key, value in fields.items():
                if value is not None:
                    query = query.where(getattr(self, key) == value)
            
            if not offset:
                query.offset(page * limit).limit(limit)
            else:
                query.offset(offset).limit(limit)
            
            query.order_by(self.id)

            results = await session.exec(query)
            return results.all()
        except Exception as e:
            logger.error(f"Error al obtener {self.__name__} por {form}: {e}")
            raise e

@event.listens_for(BaseSQLModel, "before_insert")
def before_insert(mapper, connection, target):
    target.created_at = datetime.now()
    target.updated_at = datetime.now()

@event.listens_for(BaseSQLModel, "before_update")
def before_update(mapper, connection, target):
    target.updated_at = datetime.now()