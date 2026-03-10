import json
from asyncio import run
from uuid import uuid6

from rich import traceback

from server.core.cache import rc
from server.core.database import get_session
from server.core.models.base import Log
from server.core.models.enums.base import LogAction, LogLevel, LogStatus, LogType
from server.core.utils.logger import _get_celery_logger
from ...database.main import engine
from sqlalchemy.ext.asyncio import AsyncSession
from .main import make

traceback.install()

logger = _get_celery_logger(__name__)


def _safe_enum(enum_cls, value, default):
    """Retorna el enum correspondiente al valor, o el default si es None o inválido."""
    if value is None:
        return default
    try:
        return enum_cls(value)
    except (ValueError, KeyError):
        return default


async def _async_rsave_log(data: dict):
    try:
        ID_LOG = uuid6()
        key = f"log:{ID_LOG}"
        await rc.set(key, json.dumps(data, default=str))
        await rc.expire(key, 60 * 60 * 24)
    except Exception as e:
        logger.error(f"Error al guardar log en redis: {e}")


async def _save_to_db(data: dict):
    try:
        async with AsyncSession(engine) as session:
            log = Log(
                meta=data.get("meta", {}),
                type=_safe_enum(LogType, data.get("type"), LogType.NOT_TYPE),
                level=_safe_enum(LogLevel, data.get("level"), LogLevel.NOT_LEVEL),
                status=_safe_enum(LogStatus, data.get("status"), LogStatus.NOT_STATUS),
                action=_safe_enum(LogAction, data.get("action"), LogAction.NOT_REGISTERED),
                assistant_message=data.get("assistant_message", "N/A"),
                source=data.get("source", "N/A"),
                final_message=data.get("final_message", ""),
            )
            logger.debug(f"Log={log}")
            session.add(log)
            await session.commit()
    except Exception as e:
        logger.error(f"Error interno guardando log en DB: {e}")


@make.task
def rsave_log(data: dict):
    try:
        run(_async_rsave_log(data))
    except Exception as e:
        logger.error(f"Error al ejecutar tarea save_log: {e}")


@make.task
def save_log(data: dict):
    try:
        run(_save_to_db(data))
    except Exception as e:
        logger.error(f"Error al ejecutar tarea save_log: {e}")
