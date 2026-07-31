import asyncio
from typing import Any, Optional

import httpx

from .cache import Cache


class MojangClient:
    BASE_URL = "https://api.mojang.com"
    SESSION_URL = "https://sessionserver.mojang.com"

    CACHE_TTL = 300

    def __init__(
        self,
        cache: Cache | None = None,
    ):
        self.cache = cache
        self.http: Optional[httpx.AsyncClient] = None

    async def start(self):
        if self.http is None or self.http.is_closed:
            self.http = httpx.AsyncClient(
                timeout=10.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "MojangClient/1.0",
                },
            )

    async def close(self):
        if self.http:
            await self.http.aclose()
            self.http = None

    def _make_key(
        self,
        endpoint: str,
        params: dict[str, Any],
    ) -> str:
        if self.cache:
            return self.cache.make_key(
                endpoint,
                params,
            )

        return f"{endpoint}:{params}"

    async def _request(
        self,
        url: str,
        cache_key: str,
        ttl: int = CACHE_TTL,
        retries: int = 3,
    ) -> dict[str, Any] | None:

        await self.start()

        if self.cache:
            cached = self.cache.get(cache_key)

            if cached is not None:
                return cached

        last_error = None

        for attempt in range(retries):
            try:
                response = await self.http.get(url)

                if response.status_code in (204, 404):
                    return None

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 2))
                    await asyncio.sleep(retry_after)
                    continue

                if response.status_code >= 500:
                    await asyncio.sleep(2**attempt)
                    continue

                response.raise_for_status()

                data = response.json()

                if self.cache:
                    self.cache.set(
                        cache_key,
                        data,
                        ttl,
                    )

                return data

            except (
                httpx.TimeoutException,
                httpx.NetworkError,
            ) as error:
                last_error = error
                await asyncio.sleep(2**attempt)

        if last_error:
            raise last_error

        return None

    async def get_uuid(
        self,
        username: str,
    ) -> str | None:

        username = username.lower()

        key = self._make_key(
            "mojang_username",
            {
                "username": username,
            },
        )

        data = await self._request(
            url=f"{self.BASE_URL}/users/profiles/minecraft/{username}",
            cache_key=key,
        )

        return data["id"] if data else None

    async def get_username(
        self,
        uuid: str,
    ) -> str | None:

        uuid = uuid.replace("-", "")

        key = self._make_key(
            "mojang_uuid",
            {
                "uuid": uuid,
            },
        )

        data = await self._request(
            url=f"{self.SESSION_URL}/session/minecraft/profile/{uuid}",
            cache_key=key,
        )

        return data["name"] if data else None

    async def profile(
        self,
        uuid: str,
    ) -> dict[str, Any] | None:

        uuid = uuid.replace("-", "")

        key = self._make_key(
            "mojang_profile",
            {
                "uuid": uuid,
            },
        )

        return await self._request(
            url=f"{self.SESSION_URL}/session/minecraft/profile/{uuid}",
            cache_key=key,
        )
