from discord import Embed
from discord.ext import commands, tasks

from core import colors
from core.api import mojang_client
from core.api.helpers import GuildInfo
from core.database.handlers import GuildTrackerHandler
from core.database.handlers.guild import GuildLog, TrackedPlayer


class LogsMessage:
    def __init__(
        self,
        uuid: str,
        player_name: str,
        log_type: str = "join",
    ):
        self.embed = Embed(
            color=colors.green if log_type == "join" else colors.red,
        )

        content = (
            f"{player_name} has joined the guild."
            if log_type == "join"
            else f"{player_name} has left (or was kicked) from the guild."
        )

        self.embed.set_author(
            name=content,
            url=f"https://namemc.com/profile/{uuid}",
            icon_url=f"https://nmsr.nickac.dev/face/{uuid}",
        )


class GuildLogs(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.guild_log_task.start()

    def cog_unload(self):
        self.guild_log_task.cancel()

    @tasks.loop(minutes=5)
    async def guild_log_task(self):
        handler = GuildTrackerHandler()

        guilds = handler.get_tracked_guilds()

        for guild in guilds:
            guild_info = await GuildInfo.fetch(guild.guild_id)

            if not guild_info:
                continue

            await handler.create_daily_snapshots(
                guild_info,
                guild.guild_id,
            )

            current_players = {
                member["uuid"].replace("-", "") for member in guild_info.members
            }

            stored_players = handler.get_players(guild.guild_id)

            joined = current_players - stored_players
            left = stored_players - current_players

            if joined:
                players = []

                for uuid in joined:
                    players.append(
                        TrackedPlayer(
                            uuid=uuid,
                            guild_id=guild.guild_id,
                        )
                    )

                handler.add_players(players)

            if left:
                handler.update_players_left(list(left))

            if joined or left:
                await self.send_logs(
                    guild.guild_id,
                    guild.logs_channel,
                    joined,
                    left,
                )

    @guild_log_task.before_loop
    async def before_guild_log_task(self):
        await self.client.wait_until_ready()

    async def send_logs(
        self,
        guild_id: int,
        channel_id: int | None,
        joined: set[str],
        left: set[str],
    ):
        handler = GuildTrackerHandler()

        if not channel_id:
            return

        channel = self.client.get_channel(channel_id)

        if not channel:
            return

        for uuid in joined:
            player_name = await mojang_client.get_username(uuid)
            player_name = player_name or uuid

            handler.add_log(
                GuildLog(
                    id=None,
                    guild_id=guild_id,
                    player_name=player_name,
                    log_type="join",
                )
            )

            message = LogsMessage(
                uuid,
                player_name,
                "join",
            )

            await channel.send(embed=message.embed)

        for uuid in left:
            player_name = await mojang_client.get_username(uuid)
            player_name = player_name or uuid

            handler.add_log(
                GuildLog(
                    id=None,
                    guild_id=guild_id,
                    player_name=player_name,
                    log_type="leave",
                )
            )

            message = LogsMessage(
                uuid,
                player_name,
                "leave",
            )

            await channel.send(embed=message.embed)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(GuildLogs(client))
