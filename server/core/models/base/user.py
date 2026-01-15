from .main import BaseSQLModel
from sqlmodel import Field, Relationship
from pydantic import EmailStr
from argon2 import PasswordHasher
from string import punctuation
from re import match
from .scopes import Scope
from .groups import Group
from server.config import Settings
from server.core.utils.logger import get_logger
from server.core.models.base.decorators.register import register

logger = get_logger(__name__)
hasher = PasswordHasher(
    time_cost=16,
    memory_cost=65536,
    parallelism=2,
    salt_len=16,
    hash_len=32,
)

@register(fields=["*"], tag="Users")
class User(BaseSQLModel, table=True):
    __tablename__ = "users"
    name: str = Field(max_length=30, nullable=False)
    email: EmailStr = Field(max_length=30, nullable=False, unique=True)
    password: str = Field(max_length=128, nullable=False)

    active: bool = Field(default=True, nullable=False)

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

    @property
    def password(self):
        return self.password
    
    @password.setter
    async def password(self, password: str):
        regex = fr"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[{punctuation}])(?=.{{8,}})$" if not Settings().password_regex else Settings().password_regex

        if not match(regex, password):
            logger.error(f"Password does not match regex: {regex}")
            raise ValueError("Password does not match regex")
        
        self.password = hasher.hash(password)