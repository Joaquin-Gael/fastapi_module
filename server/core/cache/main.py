from redis.asyncio import Redis

from server.core.config import settings

redis_client = Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    decode_responses=settings.redis_decode_responses,
    username=settings.redis_username,
    password=settings.redis_password,
    db=settings.redis_db[4],
)
