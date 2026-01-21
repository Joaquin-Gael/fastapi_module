from asyncio import run
from uuid import uuid6

from server.core.cache import rc
from server.core.database import get_session
from server.core.models.base import Log
from server.core.models.enums.base import LogAction, LogLevel, LogStatus, LogType
from server.core.utils.logger import _get_celery_logger

from .main import make

logger = _get_celery_logger(__name__)


@make.task
def rsave_log(data: dict):
    try:
        ID_LOG = uuid6()
        key = f"log:{ID_LOG}"
        rc.hset(key, mapping=data)
        rc.expire(key, 60 * 60 * 24)
    except Exception as e:
        logger.error(f"Error al guardar log en redis: {e}")


@make.task
def save_log(data: dict):
    async def _save_to_db():
        try:
            async for session in get_session():
                log = Log(
                    data=data["data"],
                    type=LogType(data["type"]),
                    level=LogLevel(data["level"]),
                    status=LogStatus(data["status"]),
                    action=LogAction(data["action"]),
                    assistant_message=data["assistant_message"],
                    source=data["source"],
                    final_message=data["final_message"],
                )
                logger.debug(f"Log={log}")
                session.add(log)
                await session.commit()
                break
        except Exception as e:
            logger.error(f"Error interno guardando log en DB: {e}")

    try:
        run(_save_to_db())
    except Exception as e:
        logger.error(f"Error al ejecutar tarea save_log: {e}")
