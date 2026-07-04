import re
from re import match

from argon2 import PasswordHasher
from pydantic import EmailStr, validate_email, ValidationError, field_validator
from sqlmodel import Field, Relationship

from core.config import settings
from core.models.base.decorators.register import register
from core.utils.logger import get_logger

from ..links.base.users_groups import UserGroupLink
from ..links.base.users_scopes import UserScopeLink
from .main import BaseSQLModel

logger = get_logger(__name__)
hasher = PasswordHasher(
    time_cost=16,
    memory_cost=65536,
    parallelism=2,
    salt_len=16,
    hash_len=32,
)

PUNCTUATION = r"!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"


def get_password_regex():
    """Genera el regex de validación de password."""
    return rf"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[{re.escape(PUNCTUATION)}]).{{8,}}$"

@register(fields=["*"], tag="Users")
class User(BaseSQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}
    name: str = Field(max_length=30, nullable=False)
    email: EmailStr = Field(max_length=30, nullable=False, unique=True)
    password: str = Field(max_length=128, nullable=False)

    active: bool = Field(default=True, nullable=False)

    scopes: list["Scope"] = Relationship(
        link_model=UserScopeLink,
        back_populates="users",
    )
    groups: list["Group"] = Relationship(
        link_model=UserGroupLink,
        back_populates="users",
    )

    @field_validator("email")
    @classmethod
    def v_email(cls, value: EmailStr):
        try:
            validate_email(value)
            return value
        except ValidationError:
            return ValidationError("Invalid email address")

    def verify_password(self, password: str) -> bool:
        return self.password == hasher.hash(password)

    @property
    def get_password(self):
        return self.password

    @get_password.setter
    def set_password(self, password: str):
        regex = (
            get_password_regex()
            if not settings.password_regex
            else settings.password_regex
        )

        if not match(regex, password):
            logger.error(f"Password does not match regex: {regex}")
            raise ValueError("Password does not match regex")

        self.password = hasher.hash(password)