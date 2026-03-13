import json
from typing import Any, Optional
import redis.asyncio as redis

from config.settings import loaded_config
from config.logging import logger


class RedisClient:
    """Redis client for caching and pub/sub operations."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._client = None
        return cls._instance

    async def get_client(self):
        """Get or create Redis client."""
        if self._client is None:
            self._client = await redis.from_url(
                loaded_config.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Redis client initialized")
        return self._client

    async def set_json(self, key: str, value: Any, expiration: int = None):
        """Set a JSON value in Redis."""
        try:
            client = await self.get_client()
            json_str = json.dumps(value)
            if expiration:
                await client.setex(key, expiration, json_str)
            else:
                await client.set(key, json_str)
        except Exception as e:
            logger.error(f"Redis set_json error: {e}", key=key)
            raise

    async def get_json(self, key: str) -> Optional[Any]:
        """Get a JSON value from Redis."""
        try:
            client = await self.get_client()
            value = await client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get_json error: {e}", key=key)
            raise

    async def delete(self, key: str):
        """Delete a key from Redis."""
        try:
            client = await self.get_client()
            await client.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error: {e}", key=key)
            raise

    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            logger.info("Redis connection closed")
