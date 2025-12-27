from .main import BaseSQLModel
from sqlmodel import Field, Relationship

class Group(BaseSQLModel):
    __tablename__ = "groups"
    name: str = Field(max_length=30, nullable=False)
