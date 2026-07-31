import json
from typing import Any, Optional

import redis
from cachetools import TTLCache


class Cache:
    def __init__(
        self,
        redis_host: str,
        redis_port: int,
        password: str | None = None,
        prefix: str = "cache",
        memory_ttl: int = 300,
        memory_size: int = 2000,
    ):
        self.prefix = prefix
        self.memory = TTLCache(maxsize=memory_size, ttl=memory_ttl)
        self.redis = redis.Redis(
            host=redis_host, port=redis_port, password=password, decode_responses=True
        )

        try:
            self.redis.ping()
            print("Redis connected.")
        except Exception:
            print("Redis unavailable.")

    def make_key(self, endpoint: str, params: dict[str, Any]) -> str:
        return f"{self.prefix}:{endpoint}:{json.dumps(params, sort_keys=True)}"

    def get(self, key: str) -> Optional[Any]:
        if key in self.memory:
            return self.memory[key]
        try:
            value = self.redis.get(key)

        except Exception:
            return None
        if value is None:
            return None

        try:
            data = json.loads(value)
        except Exception:
            return None

        self.memory[key] = data

        return data

    def set(self, key: str, value: Any, ttl: int = 300):
        self.memory[key] = value

        try:
            self.redis.setex(key, ttl, json.dumps(value))
        except Exception:
            pass

    def delete(self, key: str):
        self.memory.pop(key, None)

        try:
            self.redis.delete(key)
        except Exception:
            pass
