import asyncio
import datetime
import time
from dataclasses import dataclass

from core.api.helpers import PlayerInfo
from core.database import Cursor, ensure_cursor


@dataclass(slots=True)
class TrackedGuild:
    guild_id: int
    logs_channel: int | None = None


@dataclass(slots=True)
class GuildSnapshot:
    id: int | None
    guild_id: int
    gxp: int
    date: datetime.date


@dataclass(slots=True)
class TrackedPlayer:
    uuid: str
    guild_id: int | None


@dataclass(slots=True)
class PlayerSnapshot:
    id: int | None
    uuid: str
    guild_id: int
    level: int
    xp: int
    date: datetime.date


@dataclass(slots=True)
class GuildLog:
    id: int | None
    guild_id: int
    player_name: str
    log_type: str
    created_at: int | None = None


class GuildTrackerHandler:
    @ensure_cursor
    def add_guild(
        self,
        guild: TrackedGuild,
        *,
        cursor: Cursor = None,
    ) -> None:
        cursor.execute(
            """
            INSERT INTO tracked_guilds (guild_id, logs_channel)
            VALUES (%s, %s)
            """,
            (
                guild.guild_id,
                guild.logs_channel,
            ),
        )

    @ensure_cursor
    def get_guild(
        self,
        guild_id: int,
        *,
        cursor: Cursor = None,
    ) -> TrackedGuild | None:
        cursor.execute(
            """
            SELECT guild_id, logs_channel
            FROM tracked_guilds
            WHERE guild_id = %s
            """,
            (guild_id,),
        )

        result = cursor.fetchone()
        return TrackedGuild(**result) if result else None

    @ensure_cursor
    def add_snapshot(
        self,
        snapshot: GuildSnapshot,
        *,
        cursor: Cursor = None,
    ) -> None:
        cursor.execute(
            """
            INSERT INTO tracked_guild_snapshots (guild_id, gxp, date)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                gxp = VALUES(gxp)
            """,
            (
                snapshot.guild_id,
                snapshot.gxp,
                snapshot.date,
            ),
        )

    @ensure_cursor
    def add_players(
        self,
        players: list[TrackedPlayer],
        *,
        cursor: Cursor = None,
    ) -> None:
        cursor.executemany(
            """
            INSERT INTO tracked_players (uuid, guild_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
                guild_id = VALUES(guild_id)
            """,
            [
                (
                    player.uuid,
                    player.guild_id,
                )
                for player in players
            ],
        )

    @ensure_cursor
    def player_exists(
        self,
        uuid: str,
        *,
        cursor: Cursor = None,
    ) -> bool:
        cursor.execute(
            """
            SELECT 1
            FROM tracked_players
            WHERE uuid = %s
            """,
            (uuid,),
        )

        return cursor.fetchone() is not None

    @ensure_cursor
    def has_player_snapshot(
        self,
        uuid: str,
        guild_id: int,
        date: datetime.date,
        *,
        cursor: Cursor = None,
    ) -> bool:
        cursor.execute(
            """
            SELECT 1
            FROM tracked_player_snapshots
            WHERE uuid = %s
            AND guild_id = %s
            AND date = %s
            """,
            (
                uuid,
                guild_id,
                date,
            ),
        )

        return cursor.fetchone() is not None

    @ensure_cursor
    def add_player_snapshots(
        self,
        snapshots: list[PlayerSnapshot],
        *,
        cursor: Cursor = None,
    ) -> None:
        cursor.executemany(
            """
            INSERT INTO tracked_player_snapshots
                (uuid, guild_id, level, xp, date)
            VALUES
                (%s, %s, %s, %s, %s)
            """,
            [
                (
                    snapshot.uuid,
                    snapshot.guild_id,
                    snapshot.level,
                    snapshot.xp,
                    snapshot.date,
                )
                for snapshot in snapshots
            ],
        )

    async def track_players(
        self,
        guild_info,
        guild_id: int,
    ) -> None:
        semaphore = asyncio.Semaphore(5)

        async def fetch_player(member: dict):
            async with semaphore:
                uuid = member["uuid"].replace("-", "")
                return await PlayerInfo.fetch(uuid)

        players = await asyncio.gather(
            *(fetch_player(member) for member in guild_info.members)
        )

        tracked_players = []
        player_snapshots = []

        today = datetime.date.today()

        for player in players:
            if not player:
                continue

            tracked_players.append(
                TrackedPlayer(
                    uuid=player.uuid,
                    guild_id=guild_id,
                )
            )

            player_snapshots.append(
                PlayerSnapshot(
                    id=None,
                    uuid=player.uuid,
                    guild_id=guild_id,
                    level=player.level,
                    xp=player.exp,
                    date=today,
                )
            )

        if tracked_players:
            self.add_players(tracked_players)

        if player_snapshots:
            self.add_player_snapshots(player_snapshots)

    @ensure_cursor
    def get_tracked_guilds(
        self,
        *,
        cursor: Cursor = None,
    ) -> list[TrackedGuild]:
        cursor.execute(
            """
            SELECT guild_id, logs_channel
            FROM tracked_guilds
            """
        )

        return [TrackedGuild(**guild) for guild in cursor.fetchall()]

    @ensure_cursor
    def get_players(
        self,
        guild_id: int,
        *,
        cursor: Cursor = None,
    ) -> set[str]:
        cursor.execute(
            """
            SELECT uuid
            FROM tracked_players
            WHERE guild_id = %s
            """,
            (guild_id,),
        )

        return {player["uuid"] for player in cursor.fetchall()}

    @ensure_cursor
    def update_players_left(
        self,
        players: list[str],
        *,
        cursor: Cursor = None,
    ) -> None:
        cursor.executemany(
            """
            UPDATE tracked_players
            SET guild_id = NULL
            WHERE uuid = %s
            """,
            [(uuid,) for uuid in players],
        )

    @ensure_cursor
    def add_log(
        self,
        log: GuildLog,
        *,
        cursor: Cursor = None,
    ) -> None:
        cursor.execute(
            """
            INSERT INTO guild_logs (
                guild_id,
                player_name,
                log_type,
                created_at
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                log.guild_id,
                log.player_name,
                log.log_type,
                int(time.time()),
            ),
        )

    @ensure_cursor
    def get_logs(
        self,
        guild_id: int,
        limit: int = 25,
        *,
        cursor: Cursor = None,
    ) -> list[GuildLog]:
        cursor.execute(
            """
            SELECT id, guild_id, player_name, log_type, created_at
            FROM guild_logs
            WHERE guild_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (
                guild_id,
                limit,
            ),
        )

        return [GuildLog(**log) for log in cursor.fetchall()]

    async def create_daily_snapshots(
        self,
        guild_info,
        guild_id: int,
    ) -> None:
        semaphore = asyncio.Semaphore(5)

        async def fetch_player(member: dict):
            async with semaphore:
                uuid = member["uuid"].replace("-", "")
                return await PlayerInfo.fetch(uuid)

        players = await asyncio.gather(
            *(fetch_player(member) for member in guild_info.members)
        )

        snapshots = []

        today = datetime.date.today()

        for player in players:
            if not player:
                continue

            if self.has_player_snapshot(
                player.uuid,
                guild_id,
                today,
            ):
                continue

            snapshots.append(
                PlayerSnapshot(
                    id=None,
                    uuid=player.uuid,
                    guild_id=guild_id,
                    level=player.level,
                    xp=player.exp,
                    date=today,
                )
            )

        if snapshots:
            self.add_player_snapshots(snapshots)

    @ensure_cursor
    def get_players_first_week_snapshot(
        self,
        guild_id: int,
        *,
        cursor: Cursor = None,
    ) -> dict[str, PlayerSnapshot]:
        today = datetime.date.today()

        week_start = today - datetime.timedelta(days=today.weekday())

        cursor.execute(
            """
            SELECT
                s.id,
                s.uuid,
                s.guild_id,
                s.level,
                s.xp,
                s.date
            FROM tracked_players tp
            JOIN (
                SELECT
                    uuid,
                    MIN(date) AS first_date
                FROM tracked_player_snapshots
                WHERE date >= %s
                GROUP BY uuid
            ) first_snap
                ON tp.uuid = first_snap.uuid
            JOIN tracked_player_snapshots s
                ON s.uuid = first_snap.uuid
            AND s.date = first_snap.first_date
            WHERE tp.guild_id = %s
            ORDER BY s.level DESC, s.xp DESC
            """,
            (
                week_start,
                guild_id,
            ),
        )

        return {row["uuid"]: PlayerSnapshot(**row) for row in cursor.fetchall()}

    @ensure_cursor
    def get_guilds_first_week_snapshot(
        self,
        *,
        cursor: Cursor = None,
    ) -> dict[int, GuildSnapshot]:
        today = datetime.date.today()
        week_start = today - datetime.timedelta(days=today.weekday())

        cursor.execute(
            """
            SELECT
                s.id,
                s.guild_id,
                s.gxp,
                s.date
            FROM tracked_guild_snapshots AS s
            JOIN (
                SELECT
                    guild_id,
                    MIN(date) AS first_date
                FROM tracked_guild_snapshots
                WHERE date >= %s
                GROUP BY guild_id
            ) AS first_snap
                ON s.guild_id = first_snap.guild_id
            AND s.date = first_snap.first_date
            ORDER BY s.gxp DESC
            """,
            (week_start,),
        )

        return {row["guild_id"]: GuildSnapshot(**row) for row in cursor.fetchall()}

    @ensure_cursor
    def has_guild_snapshot(
        self,
        guild_id: int,
        date: datetime.date,
        *,
        cursor: Cursor = None,
    ) -> bool:
        cursor.execute(
            """
            SELECT 1
            FROM tracked_guild_snapshots
            WHERE guild_id = %s
            AND date = %s
            LIMIT 1
            """,
            (
                guild_id,
                date,
            ),
        )

        return cursor.fetchone() is not None
