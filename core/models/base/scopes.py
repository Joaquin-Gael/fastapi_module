from sqlmodel import Field, Relationship

from ..links.base.groups_scopes import GroupScopeLink
from ..links.base.users_scopes import UserScopeLink
from .groups import Group
from .main import BaseSQLModel


class Scope(BaseSQLModel, table=True):
    __tablename__ = "scopes"
    __table_args__ = {"extend_existing": True}
    name: str = Field(max_length=30, nullable=False, unique=True)
    groups: list[Group] = Relationship(
        back_populates="scopes", link_model=GroupScopeLink
    )
    users: list["User"] = Relationship(
        back_populates="scopes", link_model=UserScopeLink
    )
