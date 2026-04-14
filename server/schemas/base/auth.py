from pydantic import EmailStr, Field
from .main import BaseSchema
from uuid import UUID
from typing import Optional


class LoginRequest(BaseSchema):
    email: EmailStr
    password: str


class RegisterRequest(BaseSchema):
    name: str = Field(max_length=30)
    email: EmailStr
    password: str


class TokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseSchema):
    id: UUID
    name: str
    email: EmailStr
    active: bool


class CurrentUser(BaseSchema):
    id: UUID
    name: str
    email: EmailStr
    active: bool
    scopes: list[str] = []
    groups: list[str] = []
