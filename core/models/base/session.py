import secrets
import traceback
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from uuid import UUID

from pydantic import ValidationError
from sqlmodel import Field
from sqlalchemy import event, DateTime, func
from sqlalchemy.orm import validates

from .main import BaseSQLModel
from ...utils.logger import get_logger

logger = get_logger(__name__)

class Session(BaseSQLModel, table=True):
    code: str = Field(default_factory=lambda: secrets.token_urlsafe(64), allow_mutation=False)
    user_id: UUID = Field(foreign_key="users.id")
    dead_time: datetime = Field(
        default=datetime.now() + timedelta(hours=2), nullable=False
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            ZoneInfo("America/Argentina/Buenos_Aires")
        ),
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "name": "created_at",
            "server_default": func.now()
        }
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(
            ZoneInfo("America/Argentina/Buenos_Aires")
        ),
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "name": "updated_at",
            "server_default": func.now()
        }
    )
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(
            ZoneInfo("America/Argentina/Buenos_Aires")
        ) + timedelta(days=1),
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "name": "expires_at",
            "server_default": func.now()
        }
    )

    @validates("user_id")
    def validate_user_id(self, key, value):
        if not self.user_id and self.user_id != value:
            raise ValidationError("Cannot reassign session to different user")
        return value


@event.listens_for(Session, "before_update")
def session_changed(mapper, connection, target):
    try:
        target.updated_at = datetime.now(
            ZoneInfo("America/Argentina/Buenos_Aires")
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error(str(traceback.format_exc()))


@event.listens_for(Session, "before_insert")
def set_expire_time(mapper, connection, target):
    try:
        target.expires_at = datetime.now(
            ZoneInfo("America/Argentina/Buenos_Aires")
        ) + timedelta(days=1)
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error(str(traceback.format_exc()))