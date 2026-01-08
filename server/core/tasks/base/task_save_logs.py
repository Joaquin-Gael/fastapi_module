from .main import make
from server.core.models.base import Log
from server.core.cache import rc
from server.core.models.enums.base import LogType, LogLevel, LogStatus, LogAction
from server.core.database import get_session
from asyncio import run
from uuid import uuid6

@make.task
def rsave_log(data: dict):
    try:
        ID_LOG = uuid6()
        rc.hset(f"log:{ID_LOG}", mapping=data, ex=60*5, key=ID_LOG)
    except Exception as e:
        print(f"Error al guardar log en redis: {e}")

@make.task
def save_log(data: dict):
    async def _save_to_db():
        try:
            # Iteramos sobre el generador asíncrono get_session
            async for session in get_session():
                log = Log(**data)
                session.add(log)
                await session.commit()
                # Importante: salimos del bucle ya que get_session solo devuelve una sesión
                break
        except Exception as e:
            print(f"Error interno guardando log en DB: {e}")

    try:
        run(_save_to_db())
    except Exception as e:
        print(f"Error al ejecutar tarea save_log: {e}")