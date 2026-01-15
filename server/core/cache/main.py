from redis import Redis
from server.core.config import CoreSettings as Settings

redis_client = Redis(
    host=Settings().redis_host,
    port=Settings().redis_port,
    decode_responses=Settings().redis_decode_responses,
    username=Settings().redis_username,
    password=Settings().redis_password,
    db=Settings().redis_db[0],
)