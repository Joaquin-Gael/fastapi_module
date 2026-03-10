import json
from typing import Type

from redis.asyncio import Redis
from sqlmodel import SQLModel

from server.core.config import CoreSettings as Settings
from server.core.utils.logger import _get_celery_logger

logger = _get_celery_logger(__name__)

_register_buffer: list[str] = []


def _build_metadata(
    model: Type[SQLModel],
    tag: str,
    actions: list,
    fields: list,
) -> dict:
    model_name = model.__name__
    table_name = getattr(model, "__tablename__", model_name.lower())

    return {
        "name": model_name,
        "object_name": model_name,
        "model_module": model.__module__,
        "table_name": table_name,
        "admin_url": f"/admin/{table_name}/",
        "tag": tag,
        "actions": actions,
        "fields": [
            field
            for field in model.model_fields.keys()
            if field in fields or fields == ["*"]
        ]
        if hasattr(model, "model_fields")
        else [],
    }


def register(
    fields: list = ["*"],
    tag: str = "",
    actions: list = ["read", "write", "delete", "update", "export"],
):
    """Decorador que registra un modelo en el buffer de admin.

    No se conecta a Redis al importar; solo acumula en memoria.
    Llamar a flush_registry() en el lifespan para volcar a Redis.
    """

    def wrapper(model: Type[SQLModel]):
        try:
            metadata = _build_metadata(model, tag, actions, fields)
            metadata_json = json.dumps(metadata, sort_keys=True)
            if metadata_json not in _register_buffer:
                _register_buffer.append(metadata_json)
        except Exception as e:
            logger.debug(f"Error buffering modelo {model.__name__} en Admin: {e}")
        return model

    return wrapper


async def flush_registry() -> None:
    """Reemplaza atómicamente el set admin:registry en Redis con los modelos
    registrados en este ciclo de import.

    Modelos que fueron removidos del código no quedarán en Redis.
    Debe llamarse una vez en el lifespan de la app, después de importar todos
    los módulos con modelos decorados.
    """
    client = Redis(
        host=Settings().redis_host,
        port=Settings().redis_port,
        decode_responses=Settings().redis_decode_responses,
        username=Settings().redis_username,
        password=Settings().redis_password,
        db=Settings().redis_db[0],
    )

    try:
        # Pipeline atómico: borrar set viejo + agregar todos los buffered
        async with client.pipeline(transaction=True) as pipe:
            pipe.delete("admin:registry")
            if _register_buffer:
                pipe.sadd("admin:registry", *_register_buffer)
            await pipe.execute()

        logger.info(f"Admin registry flushed: {len(_register_buffer)} modelo(s) registrados.")
    except Exception as e:
        logger.error(f"Error flushing admin registry a Redis: {e}")
    finally:
        await client.close()
