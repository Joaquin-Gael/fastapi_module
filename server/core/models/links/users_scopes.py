from sqlmodel import Field, SQLModel
from uuid import UUID

class UserScopeLink(SQLModel, table=True):
    user_id: UUID = Field(foreign_key="users.user_id", primary_key=True)
    scope_id: UUID = Field(foreign_key="scopes.scope_id", primary_key=True)
