import asyncio
from dataclasses import dataclass
from datetime import date, timedelta

from core.api.helpers import GuildInfo, PlayerInfo
from core.database import Cursor, ensure_cursor
from core.database.handlers import GuildTrackerHandler

ROLE_PREFIXES: dict[str, list[tuple[str, str]]] = {
    "Owner": [("#ff5555", "[Owner]")],
    "Admin": [("#ff5555", "[Admin]")],
    "Manager": [("#aa0000", "[Manager]")],
    "Dev": [("#55ff55", "[Dev]")],
    "HeadBuilder": [("#aa00aa", "[HeadBuilder]")],
    "Builder": [("#ff55ff", "[Builder]")],
    "SrMod": [("#ffff55", "[SrMod]")],
    "Mod": [("#ffff55", "[Mod]")],
    "Trainee": [("#55ff55", "[Trainee]")],
    "Youtube": [
        ("#ff5555", "["),
        ("#ffffff", "Youtube"),
        ("#ff5555", "]"),
    ],
    "Master": [("#ffaa00", "[Master]")],
    "Expert": [("#5555ff", "[Expert]")],
    "Adept": [("#00aa00", "[Adept]")],
    "Legend": [
        ("#ffaa00", "[Leg"),
        ("#ffff55", "en"),
        ("#ffffff", "d"),
        ("#ffaa00", "]"),
    ],
}

ROLE_NAME_COLORS: dict[str, str] = {
    "Owner": "#ff5555",
    "Admin": "#ff5555",
    "Manager": "#aa0000",
    "Dev": "#55ff55",
    "HeadBuilder": "#aa00aa",
    "Builder": "#ff55ff",
    "SrMod": "#ffff55",
    "Mod": "#ffff55",
    "Trainee": "#55ff55",
    "Youtube": "#ff5555",
    "Master": "#ffaa00",
    "Expert": "#5555ff",
    "Adept": "#00aa00",
    "Legend": "#ffaa00",
}

DEFAULT_ROLE_COLOR = "#aaaaaa"


@dataclass(slots=True)
class TextSpan:
    text: str
    color: str


@dataclass
class GuildStats:
    total_tracked_guilds: int
    total_tracked_players: int
    total_guild_members: int | None
    total_guild_xp: int | None


@dataclass
class TrackedGuild:
    id: int
    name: str
    xp: int | None
    percentage: float


@dataclass
class TopGuild:
    name: str
    tag: str
    xp: int
    percentage: float = 0


@dataclass(slots=True)
class GuildXpChartData:
    name: str
    gained_xp: int


@dataclass(slots=True)
class GuildMember:
    username: str
    guild_role: str
    role: str
    rank_spans: list[TextSpan]
    username_spans: list[TextSpan]


def get_rank_spans(role: str) -> list[TextSpan]:
    prefix_parts = ROLE_PREFIXES.get(role)

    if not prefix_parts:
        return []

    return [
        TextSpan(
            text=text,
            color=color,
        )
        for color, text in prefix_parts
    ]


def get_username_spans(username: str, role: str) -> list[TextSpan]:
    if role == "Legend":
        if len(username) >= 3:
            return [
                TextSpan(
                    text=username[:-3],
                    color="#ffaa00",
                ),
                TextSpan(
                    text=username[-3:-1],
                    color="#ffff55",
                ),
                TextSpan(
                    text=username[-1],
                    color="#ffffff",
                ),
            ]

        return [
            TextSpan(
                text=username,
                color="#ffaa00",
            )
        ]

    return [
        TextSpan(
            text=username,
            color=ROLE_NAME_COLORS.get(role, DEFAULT_ROLE_COLOR),
        )
    ]


class GuildService:
    def __init__(self, guild_info: GuildInfo | None = None):
        self.guild_info = guild_info

    @ensure_cursor
    def get_total_tracked_guilds(self, *, cursor: Cursor = None) -> int:
        cursor.execute("SELECT COUNT(*) AS total FROM tracked_guilds")
        result = cursor.fetchone()

        return result["total"] if result else 0

    @ensure_cursor
    def get_total_tracked_players(self, *, cursor: Cursor = None) -> int:
        cursor.execute("SELECT COUNT(*) AS total FROM tracked_players")
        result = cursor.fetchone()

        return result["total"] if result else 0

    def get_total_guild_members(self) -> int | None:
        return self.guild_info.member_count if self.guild_info else None

    def get_total_guild_xp(self) -> int | None:
        return self.guild_info.xp if self.guild_info else None

    def get_stats(self) -> GuildStats:
        return GuildStats(
            total_tracked_guilds=self.get_total_tracked_guilds(),
            total_tracked_players=self.get_total_tracked_players(),
            total_guild_members=self.get_total_guild_members(),
            total_guild_xp=self.get_total_guild_xp(),
        )

    @ensure_cursor
    def get_daily_gained_gxp(self, *, cursor: Cursor = None) -> int:
        if self.guild_info is None or self.guild_info.xp is None:
            return 0

        today = date.today()

        cursor.execute(
            """
            SELECT gxp
            FROM tracked_guild_snapshots
            WHERE guild_id = %s
            AND date = %s
            LIMIT 1
            """,
            (self.guild_info.id, today),
        )

        snapshot = cursor.fetchone()

        if snapshot is None:
            return 0

        return self.guild_info.xp - snapshot["gxp"]

    @ensure_cursor
    def get_weekly_gained_gxp(self, *, cursor: Cursor = None) -> int:
        if self.guild_info is None or self.guild_info.xp is None:
            return 0

        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        cursor.execute(
            """
            SELECT gxp
            FROM tracked_guild_snapshots
            WHERE guild_id = %s
            AND date >= %s
            ORDER BY date ASC
            LIMIT 1
            """,
            (self.guild_info.id, week_start),
        )

        snapshot = cursor.fetchone()

        if snapshot is None:
            return 0

        return self.guild_info.xp - snapshot["gxp"]

    async def get_guild_members(self) -> list[GuildMember]:
        if self.guild_info is None or not self.guild_info.members:
            return []

        members_with_uuid = [
            member for member in self.guild_info.members if member.get("uuid")
        ]

        player_infos = await asyncio.gather(
            *(PlayerInfo.fetch(member["uuid"]) for member in members_with_uuid),
            return_exceptions=True,
        )

        guild_members: list[GuildMember] = []

        for member, player_info in zip(members_with_uuid, player_infos):
            if isinstance(player_info, Exception) or player_info is None:
                continue

            username = player_info.last_login_name
            role = "" if player_info.role in {None, "None"} else player_info.role

            guild_members.append(
                GuildMember(
                    username=username,
                    guild_role=member.get("role", "MEMBER"),
                    role=role,
                    rank_spans=get_rank_spans(role),
                    username_spans=get_username_spans(
                        username,
                        role,
                    ),
                )
            )

        return guild_members


class TrackedGuildService:
    @ensure_cursor
    def get_tracked_guild_ids(
        self,
        *,
        cursor: Cursor = None,
    ) -> list[int]:
        cursor.execute(
            """
            SELECT guild_id
            FROM tracked_guilds
            """
        )

        guilds = cursor.fetchall()

        return [guild["guild_id"] for guild in guilds]

    async def get_tracked_guilds(self) -> list[TrackedGuild]:
        guild_ids = self.get_tracked_guild_ids()

        guild_infos = await asyncio.gather(
            *(GuildInfo.fetch(guild_id) for guild_id in guild_ids),
            return_exceptions=True,
        )

        valid_guilds = [
            guild
            for guild in guild_infos
            if not isinstance(guild, Exception) and guild is not None
        ]

        max_xp = max(
            (guild.xp for guild in valid_guilds if guild.xp is not None),
            default=1,
        )

        tracked_guilds: list[TrackedGuild] = []

        for guild_info in guild_infos:
            if isinstance(guild_info, Exception) or guild_info is None:
                tracked_guilds.append(
                    TrackedGuild(
                        id=0,
                        name="Unknown",
                        xp=None,
                        percentage=0,
                    )
                )
                continue

            xp = guild_info.xp or 0

            tracked_guilds.append(
                TrackedGuild(
                    id=guild_info.id,
                    name=guild_info.name,
                    xp=guild_info.xp,
                    percentage=(xp / max_xp) * 100,
                )
            )

        tracked_guilds.sort(
            key=lambda guild: guild.xp if guild.xp is not None else -1,
            reverse=True,
        )

        return tracked_guilds

    async def get_guilds_xp_chart_data(
        self,
    ) -> list[GuildXpChartData]:
        snapshots = GuildTrackerHandler().get_guilds_first_week_snapshot()

        if not snapshots:
            return []

        guild_ids = list(snapshots.keys())

        guild_infos = await asyncio.gather(
            *(GuildInfo.fetch(guild_id) for guild_id in guild_ids),
            return_exceptions=True,
        )

        chart_data: list[GuildXpChartData] = []

        for guild_id, guild_info in zip(
            guild_ids,
            guild_infos,
        ):
            if isinstance(guild_info, Exception) or guild_info is None:
                continue

            if guild_info.xp is None:
                continue

            snapshot = snapshots[guild_id]
            gained_xp = guild_info.xp - snapshot.gxp

            chart_data.append(
                GuildXpChartData(
                    name=guild_info.name,
                    gained_xp=gained_xp,
                )
            )

        return sorted(
            chart_data,
            key=lambda guild: guild.gained_xp,
            reverse=True,
        )

    @staticmethod
    async def get_top_guilds(
        limit: int = 10,
    ) -> list[TopGuild]:
        data = await GuildInfo.fetch_top_guilds(limit)

        if not data or "guilds" not in data:
            print(data)
            return []

        guilds = [
            TopGuild(
                name=guild["name"],
                tag=guild["tag"].upper(),
                xp=guild["xp"],
            )
            for guild in data["guilds"]
        ]

        if guilds:
            highest_xp = guilds[0].xp

            for guild in guilds:
                guild.percentage = (guild.xp / highest_xp) * 100

        return guilds
