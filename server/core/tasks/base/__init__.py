from celery import Celery
from server.config import Settings
from server.core.utils.logger import get_logger

logger = get_logger(__name__)

celery = Celery(
    "tasks",
    broker=Settings().redis_url,
    backend=Settings().redis_url,
    log=logger,
    namespace="tasks",
)
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    enable_utc=True,
    broker_password=Settings().redis_password,
    result_backend_password=Settings().redis_password,
)
