from sqlmodel import Field, SQLModel
from uuid import UUID

class UserGroupLink(SQLModel, table=True):
    user_id: UUID = Field(foreign_key="users.id", primary_key=True)
    group_id: UUID = Field(foreign_key="groups.id", primary_key=True)
