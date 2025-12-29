from sqlmodel import Field, SQLModel

class UserScopeLink(SQLModel, table=True):
    user_id: int = Field(foreign_key="users.user_id", primary_key=True)
    scope_id: int = Field(foreign_key="scopes.scope_id", primary_key=True)
