from dataclasses import dataclass
from typing import Optional

from core.database import Cursor, ensure_cursor


@dataclass(slots=True)
class VerifiedUser:
    discord_id: int
    uuid: str | None = None


@dataclass(slots=True)
class VerifyRequest:
    message_id: int
    discord_id: int
    uuid: str


class VerifyHandler:
    def __init__(self, discord_id: int):
        self.discord_id = discord_id

    @ensure_cursor
    def verify_user(self, uuid: str, *, cursor: Cursor = None) -> None:
        cursor.execute(
            """
            INSERT INTO verified_users (discord_id, uuid)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                uuid=VALUES(uuid)
            """,
            (self.discord_id, uuid),
        )

    @ensure_cursor
    def delete_user(self, *, cursor: Cursor = None) -> None:
        cursor.execute(
            """
            DELETE FROM verified_users
            WHERE discord_id=%s
            """,
            (self.discord_id,),
        )

    @ensure_cursor
    def get_verified_user(
        self,
        *,
        cursor: Cursor = None,
    ) -> Optional[VerifiedUser]:
        cursor.execute(
            """
            SELECT *
            FROM verified_users
            WHERE discord_id=%s
            """,
            (self.discord_id,),
        )

        result = cursor.fetchone()

        return VerifiedUser(**result) if result else None


class VerifyRequestHandler:
    def __init__(self, message_id: int | None = None):
        self.message_id = message_id

    @ensure_cursor
    def create(
        self,
        discord_id: int,
        uuid: str,
        *,
        cursor: Cursor = None,
    ) -> None:
        cursor.execute(
            """
            INSERT INTO verify_requests
            (message_id, discord_id, uuid)
            VALUES (%s, %s, %s)
            """,
            (
                self.message_id,
                discord_id,
                uuid,
            ),
        )

    @ensure_cursor
    def get(
        self,
        *,
        cursor: Cursor = None,
    ) -> Optional[VerifyRequest]:
        cursor.execute(
            """
            SELECT *
            FROM verify_requests
            WHERE message_id=%s
            """,
            (self.message_id,),
        )

        result = cursor.fetchone()

        return VerifyRequest(**result) if result else None

    @ensure_cursor
    def delete(
        self,
        *,
        cursor: Cursor = None,
    ) -> None:
        cursor.execute(
            """
            DELETE FROM verify_requests
            WHERE message_id=%s
            """,
            (self.message_id,),
        )

    @ensure_cursor
    def get_by_discord_id(
        self,
        discord_id: int,
        *,
        cursor: Cursor = None,
    ) -> Optional[VerifyRequest]:
        cursor.execute(
            """
            SELECT *
            FROM verify_requests
            WHERE discord_id=%s
            """,
            (discord_id,),
        )

        result = cursor.fetchone()

        return VerifyRequest(**result) if result else None
