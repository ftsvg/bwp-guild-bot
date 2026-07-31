import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from core.database import Cursor, ensure_cursor


@dataclass(slots=True)
class WebUser:
    id: int
    discord_id: int
    uuid: str
    role: int
    username: str | None = None


@dataclass(slots=True)
class WebSession:
    user_id: int
    access_token: str
    expires_at: datetime


class WebUserHandler:
    def __init__(self, discord_id: int | None = None):
        self.discord_id = discord_id

    @ensure_cursor
    def create_user(
        self,
        uuid: str,
        role: int = 0,
        *,
        cursor: Cursor = None,
    ) -> bool:

        cursor.execute(
            """
            SELECT id
            FROM web_users
            WHERE discord_id = %s
            """,
            (self.discord_id,),
        )

        if cursor.fetchone() is not None:
            return False

        cursor.execute(
            """
            INSERT INTO web_users (
                discord_id,
                uuid,
                role
            )
            VALUES (%s, %s, %s)
            """,
            (
                self.discord_id,
                uuid,
                role,
            ),
        )

        return True

    @ensure_cursor
    def get_user(
        self,
        *,
        cursor: Cursor = None,
    ) -> WebUser | None:

        cursor.execute(
            """
            SELECT * FROM web_users
            WHERE discord_id = %s
            """,
            (self.discord_id,),
        )

        row = cursor.fetchone()

        return WebUser(**row) if row else None

    @ensure_cursor
    def get_user_by_id(
        self,
        user_id: int,
        *,
        cursor: Cursor = None,
    ) -> WebUser | None:

        cursor.execute(
            """
            SELECT * FROM web_users
            WHERE id = %s
            """,
            (user_id,),
        )

        row = cursor.fetchone()

        return WebUser(**row) if row else None

    @ensure_cursor
    def update_role(
        self,
        role: int,
        *,
        cursor: Cursor = None,
    ) -> bool:

        cursor.execute(
            """
            UPDATE web_users
            SET role = %s
            WHERE discord_id = %s
            """,
            (
                role,
                self.discord_id,
            ),
        )

        return cursor.rowcount > 0

    @ensure_cursor
    def create_magic_link(
        self,
        base_url: str,
        *,
        lifetime: int = 300,
        cursor: Cursor = None,
    ) -> str | None:

        user = self.get_user(cursor=cursor)

        if user is None:
            return None

        token = secrets.token_urlsafe(48)
        expires_at = datetime.utcnow() + timedelta(seconds=lifetime)

        cursor.execute(
            """
            INSERT INTO web_sessions (
                user_id,
                access_token,
                expires_at
            )
            VALUES (%s, %s, %s)

            ON DUPLICATE KEY UPDATE
                access_token = VALUES(access_token),
                expires_at = VALUES(expires_at)
            """,
            (
                user.id,
                token,
                expires_at,
            ),
        )

        return f"{base_url}?token={token}"

    @ensure_cursor
    def delete_user(
        self,
        *,
        cursor: Cursor = None,
    ) -> bool:

        cursor.execute(
            """
            DELETE FROM web_sessions
            WHERE user_id IN (
                SELECT id
                FROM web_users
                WHERE discord_id = %s
            )
            """,
            (self.discord_id,),
        )

        cursor.execute(
            """
            DELETE FROM web_users
            WHERE discord_id = %s
            """,
            (self.discord_id,),
        )

        return cursor.rowcount > 0


class WebSessionHandler:
    @ensure_cursor
    def validate_magic_link(
        self,
        token: str,
        *,
        cursor: Cursor = None,
    ) -> int | None:

        cursor.execute(
            """
            SELECT user_id
            FROM web_sessions
            WHERE access_token = %s
            AND expires_at > UTC_TIMESTAMP()
            """,
            (token,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        user_id = row["user_id"]

        cursor.execute(
            """
            DELETE FROM web_sessions
            WHERE user_id = %s
            """,
            (user_id,),
        )

        return user_id
