import json

# from functools import wraps
from typing import Type

from sqlmodel import SQLModel

from server.core.cache import rc


def register(
    fields: list = ["*"],
    tag: str = "",
    actions: list = ["read", "write", "delete", "update", "export"],
):
    def wrapper(model: Type[SQLModel]):
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
            if rc.sismember("admin:registry", registry_key):
                return model
            rc.sadd("admin:registry", registry_key, json.dumps(metadata))
            # rc.expire("admin:registry", 60 * 2)

        except Exception as e:
            print(f"Error registrando modelo {model.__name__} en Admin: {e}")

        return model

    return wrapper
