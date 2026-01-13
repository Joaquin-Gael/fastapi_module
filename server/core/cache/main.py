from redis import Redis
from server.config import Settings

redis_client = Redis(
    host=Settings().redis_host,
    port=Settings().redis_port,
    db=Settings().redis_db,
    password=Settings().redis_password
)