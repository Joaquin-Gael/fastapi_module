import json

from fastapi import APIRouter, Form, Request

from server.config import Settings
from server.core.cache import rc
from server.core.utils.logger import get_logger
from server.forms.logs import LogsFilterForm
from server.templates.utils import get_template
from server.core.spi.base.logs import SPILogs
from server.core import SessionDep

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])

spi_logs = SPILogs()

@router.get("/")
async def models(request: Request) -> list:
    raw_members = await rc.smembers("admin:registry")
    result: list[dict] = []
    for raw in raw_members:
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
            data.pop("model_module", None)
            result.append(data)
        except (json.JSONDecodeError, TypeError, AttributeError) as e:
            logger.error("Failed to parse model %s: %s", raw, e)
    return result


@router.post("/logs")
async def read_logs(request: Request, session: SessionDep, filter_form: LogsFilterForm = Form(...)):
    try:
        logs = await spi_logs.get_logs(session, filter_form.offset, filter_form.limit, filter_form.word_key)
        return logs
        
    except Exception as e:
        logger.error(f"Failed to read logs: {e}")
        return {"Erorr": "Not able to read logs"}
