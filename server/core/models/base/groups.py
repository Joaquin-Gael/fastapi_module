from .main import BaseSQLModel
from sqlmodel import Field, Relationship
from server.core.models.links.groups_scopes import GroupScopeLink
from server.core.models.links.users_groups import UserGroupLink

class Group(BaseSQLModel, table=True):
    __tablename__ = "groups"
    name: str = Field(max_length=30, nullable=False, unique=True)
    scopes: list["Scope"] = Relationship(back_populates="groups", link_model=GroupScopeLink)
    users: list["User"] = Relationship(back_populates="groups", link_model=UserGroupLink)
