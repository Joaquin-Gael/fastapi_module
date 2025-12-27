from .main import BaseSQLModel
from sqlmodel import Field, Relationship

class Scope(BaseSQLModel):
    __tablename__ = "scopes"
    name