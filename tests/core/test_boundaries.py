import pytest
import asyncio
from server.core.database import DATABASE_URL
from server.core.cache.main import redis_client
import time

MAX_TIMEOUT = 30
MAX_TOKEN_SIZE = 1000
MAX_CONNECTIONS = 100


async def get_pg_connection():
    from sqlalchemy.ext.asyncio import create_async_engine
    from server.core.config import CoreSettings as Settings

    engine = create_async_engine(Settings().database_url.split("?")[0], echo=False)
    return engine.connect()


@pytest.mark.asyncio
async def test_pg_connection_timeout():
    start = time.time()
    try:
        async with await get_pg_connection() as conn:
            result = await conn.execute("SELECT 1")
            await result.fetchone()
        elapsed = time.time() - start
        assert elapsed < MAX_TIMEOUT
    except Exception as e:
        pytest.fail(f"PostgreSQL connection timeout exceeded: {e}")


@pytest.mark.asyncio
async def test_redis_connection_timeout():
    start = time.time()
    try:
        ping_result = await redis_client.ping()
        assert ping_result == True
        elapsed = time.time() - start
        assert elapsed < MAX_TIMEOUT
    except Exception as e:
        pytest.fail(f"Redis connection timeout exceeded: {e}")


@pytest.mark.asyncio
async def test_pg_pool_exhaustion():
    async def create_connection():
        async with await get_pg_connection() as conn:
            return await conn.execute("SELECT 1")

    tasks = [create_connection() for _ in range(MAX_CONNECTIONS)]
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        failed_count = sum(1 for r in results if isinstance(r, Exception))
        assert failed_count < MAX_CONNECTIONS // 10
    except Exception as e:
        pytest.fail(f"PostgreSQL pool exhausted: {e}")


@pytest.mark.asyncio
async def test_redis_large_data_boundary():
    test_key = "large_data_test"
    large_data = "x" * MAX_TOKEN_SIZE

    try:
        await redis_client.set(test_key, large_data)
        retrieved_data = await redis_client.get(test_key)
        assert retrieved_data == large_data
        await redis_client.delete(test_key)
    except Exception as e:
        pytest.fail(f"Redis large data storage failed: {e}")


@pytest.mark.asyncio
async def test_pg_invalid_query():
    async with await get_pg_connection() as conn:
        try:
            result = await conn.execute("INVALID SQL QUERY")
            pytest.fail("Should have raised an exception for invalid SQL")
        except Exception:
            pass


@pytest.mark.asyncio
async def test_redis_invalid_command():
    try:
        result = await redis_client.execute_command("INVALID_REDIS_COMMAND")
        pytest.fail("Should have raised an exception for invalid Redis command")
    except Exception:
        pass


async def simulate_heavy_load(db_ops, redis_ops):
    db_tasks = [lambda: get_pg_connection() for _ in range(db_ops)]
    redis_tasks = [lambda: redis_client.ping() for _ in range(redis_ops)]

    start = time.time()

    db_results = await asyncio.gather(
        *[op() for op in db_tasks], return_exceptions=True
    )
    redis_results = await asyncio.gather(
        *[op() for op in redis_tasks], return_exceptions=True
    )

    elapsed = time.time() - start
    db_failures = sum(1 for r in db_results if isinstance(r, Exception))
    redis_failures = sum(1 for r in redis_results if isinstance(r, Exception))

    return elapsed, db_failures, redis_failures


@pytest.mark.asyncio
async def test_system_load_boundaries():
    elapsed, db_failures, redis_failures = await simulate_heavy_load(50, 100)

    assert elapsed < MAX_TIMEOUT
    assert db_failures < 5
    assert redis_failures < 5
