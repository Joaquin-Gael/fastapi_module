from .main import BaseSchema
from pydantic import Field
from uuid import UUID
from datetime import datetime
from ...core.models.enums.base import LogStatus, LogType, LogLevel, LogAction

class BaseLogSchema(BaseSchema):
    id: UUID = Field(default=None)
    created_at: datetime = Field(default=None)
    updated_at: datetime = Field(default=None)
    status: LogStatus = Field(default=LogStatus.PENDING)
    type: LogType = Field(default=LogType.NOT_TYPE)
    level: LogLevel = Field(default=LogLevel.NOT_LEVEL)
    action: LogAction = Field(default=LogAction.NOT_REGISTERED)
    message: str = Field(default="")
    final_message: str = Field(default="")