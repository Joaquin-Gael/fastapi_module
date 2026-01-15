from .main import BaseSQLModel
from sqlmodel import Field, Relationship
from server.core.models.base.groups import Group
from server.core.models.links.groups_scopes import GroupScopeLink
from server.core.models.links.users_scopes import UserScopeLink

class Scope(BaseSQLModel, table=True):
    __tablename__ = "scopes"
    name: str = Field(max_length=30, nullable=False, unique=True)
    groups: list[Group] = Relationship(back_populates="scopes", link_model=GroupScopeLink)
    users: list["User"] = Relationship(back_populates="scopes", link_model=UserScopeLink)
