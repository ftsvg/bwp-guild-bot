import asyncio
from dataclasses import dataclass

from core.api.helpers import GuildInfo, PlayerInfo
from core.database.handlers import GuildTrackerHandler


@dataclass(slots=True)
class XpChartData:
    username: str
    stars_gained: float | int


def normalize_uuid(uuid: str) -> str:
    return uuid.replace("-", "").lower()


class PlayerService:
    def __init__(
        self,
        guild_id: int | None = None,
    ):
        self.guild_id = guild_id

    def get_xp_for_level(
        self,
        level: int,
    ) -> int:
        cycle = {
            0: 1000,
            1: 2000,
            2: 3000,
            3: 4000,
            4: 5000,
        }

        cycle_level = level % 100

        if cycle_level in cycle:
            return cycle[cycle_level]

        block = level // 100

        base_xp = 5000
        increment = 500

        if block <= 20:
            return base_xp + (block * increment)

        return base_xp + (20 * increment)

    def get_total_xp(
        self,
        level: int,
        partial_xp: int = 0,
    ) -> int:
        total_xp = 0

        for lvl in range(1, level):
            total_xp += self.get_xp_for_level(lvl)

        total_xp += partial_xp

        return total_xp

    def get_xp_and_stars(
        self,
        old_level: int,
        old_xp: int,
        new_level: int,
        new_xp: int,
    ) -> tuple[int, float]:
        old_total_xp = self.get_total_xp(old_level, old_xp)
        new_total_xp = self.get_total_xp(new_level, new_xp)

        xp_gained = new_total_xp - old_total_xp
        stars_gained = round(xp_gained / 5000, 2)

        return xp_gained, stars_gained

    def get_stars_gained(
        self,
        old_level: int,
        old_xp: int,
        new_level: int,
        new_xp: int,
    ) -> float:
        _, stars_gained = self.get_xp_and_stars(
            old_level,
            old_xp,
            new_level,
            new_xp,
        )

        return stars_gained

    async def get_players_xp_chart_data(
        self,
        guild_info: GuildInfo,
    ) -> list[XpChartData]:
        guild_id = self.guild_id or guild_info.id

        if guild_id is None:
            raise ValueError("A guild ID is required")

        raw_snapshots = GuildTrackerHandler().get_players_first_week_snapshot(guild_id)

        first_snapshots = {
            normalize_uuid(uuid): snapshot for uuid, snapshot in raw_snapshots.items()
        }

        member_uuids = [
            normalize_uuid(member["uuid"])
            for member in guild_info.members
            if isinstance(member, dict) and member.get("uuid")
        ]

        players = await asyncio.gather(
            *(PlayerInfo.fetch(uuid) for uuid in member_uuids)
        )

        chart_data: list[XpChartData] = []

        for player in players:
            player_uuid = normalize_uuid(player.uuid)
            snapshot = first_snapshots.get(player_uuid)

            if snapshot is None:
                continue

            if player.last_login_name is None:
                continue

            chart_data.append(
                XpChartData(
                    username=player.last_login_name,
                    stars_gained=self.get_stars_gained(
                        old_level=snapshot.level,
                        old_xp=snapshot.xp,
                        new_level=player.level,
                        new_xp=player.exp,
                    ),
                )
            )

        return sorted(
            chart_data,
            key=lambda item: item.stars_gained,
            reverse=True,
        )
