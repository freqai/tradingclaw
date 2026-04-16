"""
Redis client for message queue and pub/sub
"""

import json
from typing import Dict, Any, Optional, List
from loguru import logger
import redis.asyncio as redis


class RedisClient:
    """Async Redis client for messaging and caching"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.PubSub] = None

    async def connect(self):
        """Connect to Redis"""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
            )
            await self.client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def publish(self, channel: str, message: Dict[str, Any]) -> int:
        """Publish message to Redis channel"""
        if not self.client:
            raise RuntimeError("Not connected to Redis")

        try:
            message_str = json.dumps(message)
            result = await self.client.publish(channel, message_str)
            logger.debug(f"Published to {channel}: {result} subscribers")
            return result
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise

    async def subscribe(self, channel: str, callback=None):
        """Subscribe to Redis channel"""
        if not self.client:
            raise RuntimeError("Not connected to Redis")

        try:
            self.pubsub = self.client.pubsub()
            await self.pubsub.subscribe(channel)
            logger.info(f"Subscribed to {channel}")

            if callback:
                asyncio.create_task(self._listen(callback))

            return self.pubsub
        except Exception as e:
            logger.error(f"Failed to subscribe: {e}")
            raise

    async def _listen(self, callback):
        """Listen for messages and call callback"""
        import asyncio

        while True:
            try:
                message = await self.pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    await callback(data)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Listen error: {e}")
                await asyncio.sleep(1)

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set key-value pair"""
        if not self.client:
            raise RuntimeError("Not connected to Redis")

        try:
            value_str = json.dumps(value)
            if expire:
                await self.client.setex(key, expire, value_str)
            else:
                await self.client.set(key, value_str)
            return True
        except Exception as e:
            logger.error(f"Failed to set key: {e}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        if not self.client:
            raise RuntimeError("Not connected to Redis")

        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get key: {e}")
            return None

    async def delete(self, *keys: str) -> int:
        """Delete keys"""
        if not self.client:
            raise RuntimeError("Not connected to Redis")

        try:
            result = await self.client.delete(*keys)
            return result
        except Exception as e:
            logger.error(f"Failed to delete keys: {e}")
            return 0

    async def lpush(self, key: str, *values: Any) -> int:
        """Push values to list (left)"""
        if not self.client:
            raise RuntimeError("Not connected to Redis")

        try:
            str_values = [json.dumps(v) for v in values]
            result = await self.client.lpush(key, *str_values)
            return result
        except Exception as e:
            logger.error(f"Failed to lpush: {e}")
            return 0

    async def rpop(self, key: str) -> Optional[Any]:
        """Pop value from list (right)"""
        if not self.client:
            raise RuntimeError("Not connected to Redis")

        try:
            value = await self.client.rpop(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to rpop: {e}")
            return None

    async def blpop(self, keys: List[str], timeout: int = 0) -> Optional[tuple]:
        """Blocking left pop from list"""
        if not self.client:
            raise RuntimeError("Not connected to Redis")

        try:
            result = await self.client.blpop(keys, timeout=timeout)
            if result:
                key, value = result
                return key, json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to blpop: {e}")
            return None

    async def hset(self, name: str, key: str, value: Any) -> int:
        """Set hash field"""
        if not self.client:
            raise RuntimeError("Not connected to Redis")

        try:
            value_str = json.dumps(value)
            result = await self.client.hset(name, key, value_str)
            return result
        except Exception as e:
            logger.error(f"Failed to hset: {e}")
            return 0

    async def hgetall(self, name: str) -> Dict[str, Any]:
        """Get all hash fields"""
        if not self.client:
            raise RuntimeError("Not connected to Redis")

        try:
            result = await self.client.hgetall(name)
            return {k: json.loads(v) for k, v in result.items()}
        except Exception as e:
            logger.error(f"Failed to hgetall: {e}")
            return {}

    async def close(self):
        """Close Redis connection"""
        if self.pubsub:
            await self.pubsub.close()
            self.pubsub = None

        if self.client:
            await self.client.close()
            self.client = None

        logger.info("Redis connection closed")
