import functools

import pymysql
from pymysql.cursors import Cursor

from core.client import cfg


def db_connect():
    return pymysql.connect(
        host=cfg.dbhost,
        port=cfg.dbport,
        user=cfg.dbuser,
        password=cfg.dbpass,
        database=cfg.dbname,
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
    )


def ensure_cursor(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        cursor: Cursor | None = kwargs.get("cursor")
        if cursor:
            return func(*args, **kwargs)

        with db_connect() as conn:
            cursor = conn.cursor()
            kwargs["cursor"] = cursor
            return func(*args, **kwargs)

    return wrapper


def async_ensure_cursor(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        cursor: Cursor | None = kwargs.get("cursor")
        if cursor:
            return await func(*args, **kwargs)

        with db_connect() as conn:
            cursor = conn.cursor()
            kwargs["cursor"] = cursor
            return await func(*args, **kwargs)

    return wrapper
