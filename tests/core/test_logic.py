import pytest
import time
import asyncio
from server.core.database import DATABASE_URL
from server.core.cache.main import redis_client

PG_SELECT_THRESHOLD = 0.05
REDIS_OP_THRESHOLD = 0.01
REDIS_MEMORY_LIMIT = 10 * 1024 * 1024
CONCURRENT_CONNECTIONS = 10
MAX_REDIS_CONNECTIONS = 100


async def get_pg_connection():
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(DATABASE_URL.split("?")[0], echo=False)
    return engine.connect()


@pytest.mark.asyncio
async def test_pg_select_performance():
    from sqlalchemy import text

    async with await get_pg_connection() as conn:
        start = time.perf_counter()
        result = await conn.execute(text("SELECT 1"))
        await result.fetchone()
        elapsed = time.perf_counter() - start
        assert elapsed < PG_SELECT_THRESHOLD


@pytest.mark.asyncio
async def test_redis_ping_performance():
    start = time.perf_counter()
    result = await redis_client.ping()
    elapsed = time.perf_counter() - start
    assert result == True
    assert elapsed < REDIS_OP_THRESHOLD


@pytest.mark.asyncio
async def test_redis_hash_performance():
    key, field, value = "hash_test", "field_1", "value_1"
    start = time.perf_counter()
    await redis_client.hset(key, field, value)
    result = await redis_client.hget(key, field)
    elapsed = time.perf_counter() - start
    assert result == value
    assert elapsed < REDIS_OP_THRESHOLD
    await redis_client.delete(key)


@pytest.mark.asyncio
async def test_redis_list_performance():
    key = "list_test"
    start = time.perf_counter()
    await redis_client.lpush(key, "item_1", "item_2", "item_3")
    result = await redis_client.lrange(key, 0, -1)
    elapsed = time.perf_counter() - start
    assert len(result) == 3
    assert elapsed < REDIS_OP_THRESHOLD
    await redis_client.delete(key)


@pytest.mark.asyncio
async def test_redis_concurrent_operations():
    async def redis_operation(i):
        await redis_client.set(f"concurrent_{i}", f"value_{i}")
        return await redis_client.get(f"concurrent_{i}")

    tasks = [redis_operation(i) for i in range(MAX_REDIS_CONNECTIONS)]
    start = time.perf_counter()
    results = await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - start
    assert len(results) == MAX_REDIS_CONNECTIONS
    assert elapsed < MAX_REDIS_CONNECTIONS * REDIS_OP_THRESHOLD

    for i in range(MAX_REDIS_CONNECTIONS):
        await redis_client.delete(f"concurrent_{i}")


@pytest.mark.asyncio
async def test_pg_concurrent_connections():
    from sqlalchemy import text

    async def test_connection():
        async with await get_pg_connection() as conn:
            result = await conn.execute(text("SELECT 1"))
            await result.fetchone()

    tasks = [test_connection() for _ in range(CONCURRENT_CONNECTIONS)]
    start = time.perf_counter()
    await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - start
    assert elapsed < CONCURRENT_CONNECTIONS * PG_SELECT_THRESHOLD


@pytest.mark.asyncio
async def test_redis_memory_usage_boundary():
    for i in range(100):
        await redis_client.set(f"mem_boundary_{i}", "x" * 100)

    info = await redis_client.info("memory")
    used_memory = int(info["used_memory"])
    assert used_memory < REDIS_MEMORY_LIMIT
    await redis_client.flushdb()


@pytest.mark.asyncio
async def test_redis_expiration_performance():
    key, value = "expire_test", "test_value"
    start = time.perf_counter()
    await redis_client.set(key, value, ex=1)
    result = await redis_client.get(key)
    elapsed = time.perf_counter() - start
    assert result == value
    assert elapsed < REDIS_OP_THRESHOLD

    await asyncio.sleep(2)
    expired_result = await redis_client.get(key)
    assert expired_result is None
