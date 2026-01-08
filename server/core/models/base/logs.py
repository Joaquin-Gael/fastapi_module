from .main import BaseSQLModel
from sqlmodel import Field
from sqlalchemy.dialects.postgresql import JSON, ENUM
from pydantic import field_validator
from server.core.models.enums.base import LogType, LogLevel, LogStatus, LogAction

class Log(BaseSQLModel, table=True):
    __tablename__ = "logs"
    meta: dict = Field(
        sa_type=JSON,
        default_factory=dict,
        nullable=False,
        description="Metadata del log",
        sa_type=ENUM(LogType, name="log_type"),
    )
    type: LogType = Field(
        default=LogType.INFO,
        nullable=False,
        description="Tipo de log",
        sa_type=ENUM(LogType, name="log_type"),
    )
    level: LogLevel = Field(
        default=LogLevel.MEDIUM,
        nullable=False,
        description="Nivel de log",
        sa_type=ENUM(LogLevel, name="log_level"),
    )
    status: LogStatus = Field(
        default=LogStatus.NOT_STATUS,
        nullable=False,
        description="Estado del log",
        sa_type=ENUM(LogStatus, name="log_status"),
    )
    action: LogAction = Field(
        default=LogAction.NOT_REGISTERED,
        nullable=False,
        description="Acción del log",
        sa_type=ENUM(LogAction, name="log_action"),
    )
    assistant_message: str = Field(
        default="N/A",
        nullable=False,
        description="Mensaje del asistente-IA",
    )
    source: str = Field(
        default="N/A",
        nullable=False,
        description="Origen del log",
    )
    final_message: str = Field(
        default="N/A",
        nullable=False,
        description="Mensaje final del log",
    )

    @field_validator("type")
    def validate_type(cls, value: LogType | str | None):
        if value is None:
            return LogType.INFO
        if isinstance(value, str):
            return LogType(value)
        return value
    
    @field_validator("level")
    def validate_level(cls, value: LogLevel | str | None):
        if value is None:
            return LogLevel.MEDIUM
        if isinstance(value, str):
            return LogLevel(value)
        return value
    
    @field_validator("status")
    def validate_status(cls, value: LogStatus | str | None):
        if value is None:
            return LogStatus.NOT_STATUS
        if isinstance(value, str):
            return LogStatus(value)
        return value
    
    @field_validator("action")
    def validate_action(cls, value: LogAction | str | None):
        if value is None:
            return LogAction.NOT_REGISTERED
        if isinstance(value, str):
            return LogAction(value)
        return value