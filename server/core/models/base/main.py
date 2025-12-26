from sqlmodel import SQLModel, Field
from sqlalchemy.dialects.postgresql import UUID as PSUUID
from sqlalchemy.orm import declared_attr, mapped_column, Mapped
from uuid import UUID, uuid5

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
