import functools
import os
from typing import Any, Awaitable, Callable, TypeVar

import aiomysql
from aiomysql import Cursor, Pool
from dotenv import load_dotenv

load_dotenv()

T = TypeVar("T")


class Database:
    def __init__(self) -> None:
        self.pool: Pool | None = None

    async def init(self) -> None:
        if self.pool is not None:
            return

        self.pool = await aiomysql.create_pool(
            host=os.environ["DBENDPOINT"],
            port=int(os.environ["DBPORT"]),
            user=os.environ["DBUSER"],
            password=os.environ["DBPASS"],
            db=os.environ["DBNAME"],
            autocommit=True,
            minsize=2,
            maxsize=10,
        )

    async def close(self) -> None:
        if self.pool is None:
            return

        self.pool.close()
        await self.pool.wait_closed()
        self.pool = None

    def ensure_cursor(
        self,
        func: Callable[..., Awaitable[T]],
    ) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            cursor: Cursor | None = kwargs.get("cursor")

            if cursor is not None:
                return await func(*args, **kwargs)

            if self.pool is None:
                raise RuntimeError("Database has not been initialized.")

            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    kwargs["cursor"] = cursor
                    return await func(*args, **kwargs)

        return wrapper


db = Database()
ensure_cursor = db.ensure_cursor
