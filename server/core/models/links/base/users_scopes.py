from sqlmodel import Field, SQLModel
from uuid import UUID

class UserScopeLink(SQLModel, table=True):
    user_id: UUID = Field(foreign_key="users.id", primary_key=True)
    scope_id: UUID = Field(foreign_key="scopes.id", primary_key=True)
