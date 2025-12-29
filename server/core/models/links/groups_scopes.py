from sqlmodel import Field, SQLModel

class GroupScopeLink(SQLModel, table=True):
    group_id: int = Field(foreign_key="groups.group_id", primary_key=True)
    scope_id: int = Field(foreign_key="scopes.group_id", primary_key=True)
