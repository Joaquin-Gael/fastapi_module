from sqlmodel import Field, SQLModel

class UserGroupLink(SQLModel, table=True):
    user_id: int = Field(foreign_key="users.user_id", primary_key=True)
    group_id: int = Field(foreign_key="groups.group_id", primary_key=True)
