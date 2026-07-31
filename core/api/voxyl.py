import asyncio
import os
from typing import Any, Optional

import httpx
from dotenv import load_dotenv

from .cache import Cache
from .endpoints import VoxylApiEndpoint

load_dotenv()


class VoxylClient:
    def __init__(
        self,
        cache: Cache,
        *,
        base_url: str = "https://api.voxyl.net",
        api_keys: list[str] | None = None,
    ):
        self.base_url = base_url
        self.api_keys = api_keys or [
            os.getenv("API_KEY"),
            os.getenv("API_KEY_2"),
        ]

        self.cache = cache
        self.http: Optional[httpx.AsyncClient] = None

        self._key_usage: dict[str, int] = {k: 0 for k in self.api_keys if k}

    async def start(self):
        if self.http is None or self.http.is_closed:
            self.http = httpx.AsyncClient(
                timeout=10.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "VoxlyticsClient/1.0",
                },
            )

    async def close(self):
        if self.http:
            await self.http.aclose()
            self.http = None

    def _cache_key(
        self,
        endpoint: VoxylApiEndpoint,
        params: dict,
    ) -> str:
        return self.cache.make_key(
            endpoint.value,
            params,
        )

    def _get_best_key(self) -> str:
        return min(
            self._key_usage,
            key=self._key_usage.get,
        )

    async def request(
        self,
        endpoint: VoxylApiEndpoint,
        *,
        ttl: int = 300,
        retries: int = 3,
        **params,
    ) -> Any:

        await self.start()

        cache_key = self._cache_key(
            endpoint,
            params,
        )

        cached = self.cache.get(cache_key)

        if cached is not None:
            return cached

        url = f"{self.base_url}/{endpoint.value.format(**params)}"

        last_error = None

        for attempt in range(retries):
            api_key = self._get_best_key()

            request_params = dict(params)
            request_params["api"] = api_key

            try:
                response = await self.http.get(
                    url,
                    params=request_params,
                )

                text = response.text

                if response.status_code == 200:
                    try:
                        data = response.json()
                    except Exception:
                        data = text

                    self.cache.set(
                        cache_key,
                        data,
                        ttl,
                    )

                    remaining = response.headers.get("X-RateLimit-Remaining")

                    if remaining is not None:
                        try:
                            self._key_usage[api_key] = 1000 - int(remaining)
                        except Exception:
                            self._key_usage[api_key] += 1
                    else:
                        self._key_usage[api_key] += 1

                    return data

                if response.status_code == 429:
                    self._key_usage[api_key] += 1000
                    await asyncio.sleep(2**attempt)
                    continue

                return {
                    "error": response.status_code,
                    "data": text,
                }

            except Exception as error:
                last_error = error
                await asyncio.sleep(2**attempt)

        return {
            "error": "request_failed",
            "detail": str(last_error),
        }
