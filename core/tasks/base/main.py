from celery import Celery
from core.config import settings
from core.utils.logger import _get_celery_logger

logger = _get_celery_logger("celery.tasks")

make = Celery(
    "tasks",
    broker=settings.get_redis_broker_url,
    backend=settings.get_redis_url(3),
    include=[
        "core.tasks.base.task_save_logs",
    ],
    #log=logger,
)

make.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    broker_password=settings.redis_password if settings.redis_password else "",
    result_backend_password=settings.redis_password if settings.redis_password else "",
    timezone="America/Argentina/Buenos_Aires",
    namespace="tasks"
)
