from sqlmodel import Field, SQLModel
from uuid import UUID

class UserGroupLink(SQLModel, table=True):
    user_id: UUID = Field(foreign_key="users.user_id", primary_key=True)
    group_id: UUID = Field(foreign_key="groups.group_id", primary_key=True)
