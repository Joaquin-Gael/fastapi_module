from fastapi import APIRouter, Request
from pathlib import Path
from server.config import Settings
from server.templates.utils import get_template


router = APIRouter(prefix="/admin", tags=["Admin"])


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

@router.get("/")
async def admin_index(request: Request):
    apps = get_mock_apps()
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
    log_file = Path("data/server.log")
    logs = []
    if log_file.exists():
        try:
            # Leer las últimas 1000 líneas
            with open(log_file, "r", encoding="utf-8") as f:
                all_logs = f.readlines()
                
            # Filtrar si hay query
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
