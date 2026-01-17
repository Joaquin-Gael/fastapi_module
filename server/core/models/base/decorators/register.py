import json
#from functools import wraps
from typing import Type
from sqlmodel import SQLModel
from server.core.cache import rc

_REGISTERED_MODELS = set()

def register(fields: list = ["*"], tag: str = "", actions: list = ["read", "write", "delete", "update", "export"]):
    """
    Decorador de clase para registrar modelos automáticamente en el panel de administración.
    
    Se ejecuta una sola vez en el momento de la definición de la clase (import time).
    Guarda los metadatos del modelo en Redis para que el panel de admin los consuma.
    """
    
    # @wraps(model)  # removed: no target 'model' in scope here
    def wrapper(model: Type[SQLModel]):
        if model in _REGISTERED_MODELS:
            return model

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
                "fields": [field for field in model.model_fields.keys() if field in fields or fields == ["*"]] if hasattr(model, "model_fields") else []
            }

            registry_key = f"{hash(model_name)}-{table_name}"
            if rc.hget("admin:registry", registry_key):
                return model
            rc.hset("admin:registry", registry_key, json.dumps(metadata))
            rc.expire("admin:registry", 30)
            
            _REGISTERED_MODELS.add(model)
            

        except Exception as e:
            print(f"Error registrando modelo {model.__name__} en Admin: {e}")

        return model
    
    return wrapper
