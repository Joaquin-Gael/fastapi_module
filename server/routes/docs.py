from fastapi import APIRouter, Request
from server.templates.utils import get_template
from server.config import Settings

router = APIRouter(prefix="/scalar", tags=["Docs"])
settings = Settings()


@router.get("/")
async def doc_index(request: Request):
    return get_template(
        request, ["docs", "index.html"], {"openapi_url": settings.openapi_url}
    )


@router.get("/openapi.json")
async def get_openapi():
    """Obtener el esquema OpenAPI directamente"""
    from server.main import app

    return app.openapi()


@router.get("/health")
async def health_check():
    """Endpoint de verificación de salud del servidor"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
    }
