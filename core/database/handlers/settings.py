from dataclasses import dataclass
from typing import Literal

from core.database import Cursor, ensure_cursor

type SettingType = Literal[
    "verification",
    "applications",
    "charts",
    "gxp_updates",
    "streak",
    "counting",
    "lactate",
    "guild_role",
]


@dataclass(slots=True)
class Settings:
    guild_id: int
    verification: int | None
    applications: int | None
    charts: int | None
    gxp_updates: int | None
    streak: int | None
    counting: int | None
    lactate: int | None
    guild_role: int | None


class SettingsHandler:
    def __init__(self, guild_id: int):
        self.guild_id = guild_id

    @ensure_cursor
    def set_setting(
        self, setting: SettingType, value: int | None, *, cursor: Cursor = None
    ) -> None:
        cursor.execute(
            f"""
            INSERT INTO settings (guild_id, {setting})
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                {setting}=VALUES({setting})
            """,
            (self.guild_id, value),
        )

    @ensure_cursor
    def get_settings(self, *, cursor: Cursor = None) -> Settings:
        cursor.execute("SELECT * FROM settings WHERE guild_id=%s", (self.guild_id,))

        row = cursor.fetchone()

        if not row:
            cursor.execute(
                "INSERT INTO settings (guild_id) VALUES (%s)", (self.guild_id,)
            )

            cursor.execute("SELECT * FROM settings WHERE guild_id=%s", (self.guild_id,))

            row = cursor.fetchone()

        return Settings(**row)
