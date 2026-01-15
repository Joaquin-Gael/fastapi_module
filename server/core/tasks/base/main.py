from celery import Celery
from server.config import Settings
from server.core.utils.logger import get_logger

logger = get_logger(__name__)

make = Celery(
    "tasks",
    broker=f"redis://:{Settings().redis_password}@{Settings().redis_host}:{Settings().redis_port}/0",
    backend=f"redis://:{Settings().redis_password}@{Settings().redis_host}:{Settings().redis_port}/0",
    log=logger,
    namespace="tasks",
)
make.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    enable_utc=True,
    broker_password=Settings().redis_password,
    result_backend_password=Settings().redis_password,
)