import json

# from contextlib import ContextVar
from typing import Type

from redis import Redis as RedisSync
from redis.asyncio import Redis
from sqlmodel import SQLModel

from server.core.config import CoreSettings as Settings
from server.core.utils.async_runner import run_async
from server.core.utils.logger import _get_celery_logger

logger = _get_celery_logger(__name__)

# register_buffer: ContextVar[dict] = ContextVar("register_buffer", default={}) TODO: ver como hacer para que se eliminen los registros que no seran registrados de la recarga


async def _register_model(
    model: Type[SQLModel],
    tag: str = "",
    actions: list = ["read", "write", "delete", "update", "export"],
    fields: list = ["*"],
):
    client = Redis(
        host=Settings().redis_host,
        port=Settings().redis_port,
        decode_responses=Settings().redis_decode_responses,
        username=Settings().redis_username,
        password=Settings().redis_password,
        db=Settings().redis_db[0],
    )

    try:
        model_name = model.__name__
        table_name = getattr(model, "__tablename__", model_name.lower())

        metadata = {
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

        registry_key = f"{model_name}-{table_name}"
        if await client.sismember("admin:registry", registry_key):
            return model
        await client.sadd("admin:registry", registry_key, json.dumps(metadata))

    except Exception as e:
        logger.debug(f"Error registrando modelo {model.__name__} en Admin: {e}")
    finally:
        await client.close()

    return model


RESETED = False


def register(
    fields: list = ["*"],
    tag: str = "",
    actions: list = ["read", "write", "delete", "update", "export"],
):
    global RESETED

    sync_client = RedisSync(
        host=Settings().redis_host,
        port=Settings().redis_port,
        decode_responses=Settings().redis_decode_responses,
        username=Settings().redis_username,
        password=Settings().redis_password,
        db=Settings().redis_db[0],
    )

    if not RESETED:
        sync_client.delete("admin:registry")
        RESETED = True
    sync_client.close()

    def wrapper(model: Type[SQLModel]):
        return run_async(_register_model(model, tag, actions, fields))

    return wrapper
