from .main import BaseSchema
from uuid import UUID
from typing import Optional
from pydantic import EmailStr, Field

class BaseUserSchema(BaseSchema):
    id: Optional[UUID] = None
    name: Optional[str] = Field(max_length=30, nullable=False)
    email: Optional[EmailStr] = Field(max_length=30, nullable=False, unique=True)
    password: Optional[str] = Field(max_length=128, nullable=False)

    avtive: Optional[bool] = Field(default=True, nullable=False)

    scopes: Optional[list] = Field(default_factory=list, nullable=False)
    groups: Optional[list] = Field(default_factory=list, nullable=False)