from rich import traceback
from sqlmodel import Field, Relationship

from server.core.models.base.decorators.register import register
from server.core.models.links.groups_scopes import GroupScopeLink
from server.core.models.links.users_groups import UserGroupLink

from .main import BaseSQLModel

traceback.install()


@register(fields=["*"], tag="Group")
class Group(BaseSQLModel, table=True):
    __tablename__ = "groups"
    __table_args__ = {"extend_existing": True}
    name: str = Field(max_length=30, nullable=False, unique=True)
    scopes: list["Scope"] = Relationship(
        back_populates="groups", link_model=GroupScopeLink
    )
    users: list["User"] = Relationship(
        back_populates="groups", link_model=UserGroupLink
    )
