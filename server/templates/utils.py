from typing import Any
from fastapi.templating import Jinja2Templates
from fastapi import Response, Request
from server.config import Settings

templates = Jinja2Templates(directory=Settings().template_dir_full)

def get_template(request: Request, path: list[str], context: dict[str, Any]={}) -> Response:
    # Usamos "/" como separador universal para Jinja2, incluso en Windows
    return templates.TemplateResponse(request, "/".join(path), context)