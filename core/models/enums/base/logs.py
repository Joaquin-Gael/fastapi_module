from enum import Enum

class LogType(Enum):
    INFO = "info"
    ERROR = "error"
    WARNING = "warning"
    DEBUG = "debug"
    NOT_TYPE = "not_type"

class LogLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"
    NOT_LEVEL = "not_level"

class LogStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"
    NOT_STATUS = "not_status"

class LogAction(Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    NOT_REGISTERED = "not_registered"