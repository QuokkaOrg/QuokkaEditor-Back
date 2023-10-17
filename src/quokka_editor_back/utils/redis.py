from redis.asyncio import Redis


async def get_redis() -> Redis:
    redis = await Redis(host="redis", port=6379)
    return redis
