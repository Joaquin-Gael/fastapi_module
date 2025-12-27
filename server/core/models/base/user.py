from .main import BaseSQLModel
from sqlmodel import Field, Relationship
from pydantic import EmailStr
from argon2 import PasswordHasher
import re
from .scopes import Scope
from .groups import Group

class BaseUser(BaseSQLModel, table=False):
    name: str = Field(max_length=30, nullable=False)
    email: EmailStr = Field(max_length=30, nullable=False)
    password: str = Field(max_length=128, nullable=False)

    avtive: bool = Field(default=True, nullable=False)

    scopes: list["Scope"] = Relationship(
        link_model=Scope,
        back_populates="users",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    groups: list["Group"] = Relationship(
        link_model=Group,
        back_populates="users",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
