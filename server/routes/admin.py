from fastapi import APIRouter, Request
from pathlib import Path
from server.config import Settings
from server.templates.utils import get_template


router = APIRouter(prefix="/admin", tags=["Admin"])


from server.core.cache import rc
import json

def get_mock_apps():
    """
    Simula la estructura de aplicaciones y modelos de Django.
    En una app real, esto vendría de la base de datos o configuración.
    """
    return [
        {
            "name": "Autenticación y Autorización",
            "app_label": "auth",
            "models": [
                {"name": "Usuarios", "object_name": "User", "perms": {"add": True, "change": True, "delete": True}, "admin_url": "/admin/auth/user/"},
                {"name": "Grupos", "object_name": "Group", "perms": {"add": True, "change": True, "delete": False}, "admin_url": "/admin/auth/group/"},
            ]
        },
        {
            "name": "Gestión de Contenido",
            "app_label": "blog",
            "models": [
                {"name": "Artículos", "object_name": "Post", "perms": {"add": True, "change": True, "delete": True}, "admin_url": "/admin/blog/post/"},
                {"name": "Comentarios", "object_name": "Comment", "perms": {"add": False, "change": True, "delete": True}, "admin_url": "/admin/blog/comment/"},
                {"name": "Categorías", "object_name": "Category", "perms": {"add": True, "change": True, "delete": True}, "admin_url": "/admin/blog/category/"},
            ]
        },
        {
            "name": "Sistema",
            "app_label": "core",
            "models": [
                {"name": "Configuración", "object_name": "Config", "perms": {"add": False, "change": True, "delete": False}, "admin_url": "/admin/core/config/"},
                {"name": "Logs de Auditoría", "object_name": "AuditLog", "perms": {"add": False, "change": False, "delete": False}, "admin_url": "/admin/core/logs/"},
            ]
        }
    ]

def get_registered_apps():
    """
    Recupera la estructura de aplicaciones y modelos desde Redis,
    poblada por el decorador @register.
    """
    apps_dict = {}
    
    # Obtenemos todos los modelos registrados
    registry = rc.hgetall("admin:registry")
    
    for key, value in registry.items():
        # key es 'app_label.model_name' (bytes)
        # value es metadata json (bytes)
        try:
            metadata = json.loads(value)
            app_label = metadata["app_label"]
            
            if app_label not in apps_dict:
                apps_dict[app_label] = {
                    "name": app_label.capitalize(), # Podríamos tener un mapa de nombres bonitos
                    "app_label": app_label,
                    "models": []
                }
            
            apps_dict[app_label]["models"].append(metadata)
        except Exception as e:
            print(f"Error procesando registro admin {key}: {e}")
            
    # Convertir dict a lista y ordenar
    apps_list = list(apps_dict.values())
    apps_list.sort(key=lambda x: x["name"])
    
    # Si Redis está vacío, devolvemos los mocks por defecto para que no se vea vacío el demo
    if not apps_list:
        return get_mock_apps()
        
    return apps_list

@router.get("/")
async def admin_index(request: Request):
    apps = get_registered_apps()
    return get_template(request, ["admin", "index.html"], {
        "apps": apps,
        "title": "Administración del Sitio",
        "site_header": "FastAPI Admin",
        "has_permission": True 
    })

@router.get("/login")
async def admin_login(request: Request):
    return get_template(request, ["admin", "login.html"], {
        "title": "Iniciar Sesión"
    })

@router.get("/logs")
async def admin_logs(request: Request, q: str = ""):
    log_file = Path(Settings().log_file)
    logs = []
    if log_file.exists():
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                all_logs = f.readlines()
                
            if q:
                logs = [line for line in all_logs if q.lower() in line.lower()]
                # Limitamos a 1000 resultados filtrados
                logs = logs[-1000:]
            else:
                logs = all_logs[-1000:]
                
        except Exception:
            logs = ["Error leyendo el archivo de logs."]
    else:
        logs = ["No hay logs disponibles aún."]

    return get_template(request, ["admin", "logs.html"], {
        "title": "Logs del Sistema",
        "logs": logs,
        "site_header": "FastAPI Admin",
        "query": q
    })
