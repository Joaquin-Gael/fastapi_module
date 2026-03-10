import secrets
import string
from datetime import datetime, timedelta
from uuid import UUID

from sqlmodel import Field

from .main import BaseSQLModel


def _gen_session_code():
    code_lenght: int = 64
    return "".join([secrets.choice(string.printable) for _ in range(code_lenght)])


class Session(BaseSQLModel, table=True):
    code: Field(default_factory=lambda: _gen_session_code(), allow_mutation=False)
    user_id: UUID = Field(foreign_key="users.id")
    dead_time: datetime = Field(
        default=datetime.now() + timedelta(hours=2), nullable=False
    )
