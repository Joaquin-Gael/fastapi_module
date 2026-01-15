from sqlmodel import Field, SQLModel
from uuid import UUID

class GroupScopeLink(SQLModel, table=True):
    group_id: UUID = Field(foreign_key="groups.group_id", primary_key=True)
    scope_id: UUID = Field(foreign_key="scopes.scope_id", primary_key=True)
