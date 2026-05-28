from sqlmodel import Field, SQLModel
from uuid import UUID

class GroupScopeLink(SQLModel, table=True):
    group_id: UUID = Field(foreign_key="groups.id", primary_key=True)
    scope_id: UUID = Field(foreign_key="scopes.id", primary_key=True)
