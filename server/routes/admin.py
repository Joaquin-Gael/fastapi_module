import json

from fastapi import APIRouter, Form, Request

from server.config import Settings
from server.core.cache import rc
from server.core.utils.logger import get_logger
from server.forms.logs import LogsFilterForm
from server.templates.utils import get_template

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/")
async def models(request: Request) -> list:
    models_list = rc.smembers("admin:registry")

    models_list = list(models_list)
    logger.debug(f"Models {[model for model in models_list]}")
    for idx, model in enumerate(models_list):
        try:
            model = json.loads(model) if not isinstance(model, dict) else model
        except json.decoder.JSONDecodeError as e:
            logger.error("Failed to parse model %s: %s", model, e)
            del models_list[idx]
            continue
        models_list[idx] = model
    return models_list


@router.get("/logs")
async def read_logs(request: Request, filter_form: LogsFilterForm = Form(...)):
    pass
