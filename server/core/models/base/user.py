from .main import BaseSQLModel
from sqlmodel import Field, Relationship
from pydantic import EmailStr
from argon2 import PasswordHasher
import re

class BaseUser(BaseSQLModel, table=False):
    name: str = Field(max_length=30, nullable=False)
    email: EmailStr = Field(max_length=30, nullable=False)
    password: str = Field(max_length=128, nullable=False)

    avtive: bool = Field(default=True, nullable=False)

    scopes
    groups