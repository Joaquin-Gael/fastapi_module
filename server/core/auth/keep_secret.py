from jwt import JWT

from server.config import Settings

from ..utils.logger import get_logger

logger = get_logger(__name__)

_jwt = JWT()


async def get_token(data: dict):
    try:
        pass
    except Exception as e:
        logger.error(f"{e}")
