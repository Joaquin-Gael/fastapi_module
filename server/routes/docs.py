from fastapi import APIRouter, Request
from server.templates.utils import get_template
from server.config import Settings

router = APIRouter(prefix="/scalar", tags=["Docs"])

@router.get("/")
async def doc_index(request: Request):
    return get_template(request, ["docs", "index.html"], {"openapi_url": Settings().openapi_url})
