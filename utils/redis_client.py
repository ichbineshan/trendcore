from urllib.parse import urlparse
import redis.asyncio as redis
from contextlib import asynccontextmanager
from config.settings import loaded_config


class RedisClient:
    """
    A class that manages Redis operations with an async client.
    """

    def __init__(self):
        redis_url = loaded_config.redis_url
        parsed_url = urlparse(redis_url)
        self.redis_host = parsed_url.hostname
        self.redis_port = parsed_url.port
        self.redis_db = (
            int(parsed_url.path.strip("/")) if parsed_url.path.strip("/") else 0
        )

        self.pool = redis.ConnectionPool(
            host=self.redis_host,
            port=self.redis_port,
            db=self.redis_db,
            decode_responses=True,
            max_connections=100,  # Increased from 20 to 50 (balanced approach)
            retry_on_timeout=True,
            socket_keepalive=True,
            socket_keepalive_options={},
            health_check_interval=30,  # Health check every 30 seconds
            socket_connect_timeout=10,  # Connection timeout
            socket_timeout=30,  # Socket timeout
        )
        
        self.client = redis.Redis(connection_pool=self.pool)

    @asynccontextmanager
    async def connect(self):
        """
        Provides an async Redis client via a context manager.
        """
        try:
            yield self.client
        finally:
            await self.client.close()

    async def add_key(self, key: str, value: str, expiration: int = None):
        """
        Adds a key-value pair to Redis with an optional expiration time.

        :param key: The key to add.
        :param value: The value to associate with the key.
        :param expiration: Expiration time in seconds (optional).
        """
        async with self.connect() as client:
            if expiration:
                await client.set(key, value, ex=expiration)
            else:
                await client.set(key, value)

    async def delete_key(self, key: str):
        """
        Deletes a key from Redis.

        :param key: The key to delete.
        """
        async with self.connect() as client:
            await client.delete(key)

    async def exists_key(self, key: str) -> bool:
        """
        Deletes a key from Redis.

        :param key: The key to delete.
        """
        async with self.connect() as client:
            return await client.exists(key)

    async def get_key(self, key: str):
        """
        Retrieves the value of a key from Redis.

        :param key: The key to retrieve.
        :return: The value of the key, or None if the key does not exist.
        """
        async with self.connect() as client:
            value = await client.get(key)
            return value if value else None

    # Direct access methods for streaming scenarios where connection should persist
    async def set_key_direct(self, key: str, value: str, expiration: int = None):
        """
        Sets a key-value pair directly without closing the connection.
        Use this for streaming scenarios where the connection needs to persist.
        """
        if expiration:
            await self.client.set(key, value, ex=expiration)
        else:
            await self.client.set(key, value)

    async def get_key_direct(self, key: str):
        """
        Gets a key value directly without closing the connection.
        Use this for streaming scenarios where the connection needs to persist.
        """
        value = await self.client.get(key)
        return value if value else None

    async def lrange_direct(self, key: str, start: int, end: int):
        """
        Gets a range from a list directly without closing the connection.
        Use this for streaming scenarios where the connection needs to persist.
        """
        return await self.client.lrange(key, start, end)

    async def rpush_direct(self, key: str, *values):
        """
        Pushes values to the right of a list directly without closing the connection.
        Use this for streaming scenarios where the connection needs to persist.
        """
        return await self.client.rpush(key, *values)

    async def delete_key_direct(self, key: str):
        """
        Deletes a key directly without closing the connection.
        Use this for streaming scenarios where the connection needs to persist.
        """
        return await self.client.delete(key)

    async def expire_direct(self, key: str, seconds: int):
        """
        Sets expiration on a key directly without closing the connection.
        Use this for streaming scenarios where the connection needs to persist.
        
        :param key: The key to set expiration on
        :param seconds: Expiration time in seconds
        :return: True if the timeout was set, False if the key doesn't exist
        """
        return await self.client.expire(key, seconds)

    async def close(self):
        """
        Closes the Redis connection.
        Call this when you're done with the client.
        """
        await self.client.close()
