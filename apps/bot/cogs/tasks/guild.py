import datetime

from discord.ext import commands, tasks

from core.api.helpers import GuildInfo
from core.database.handlers import GuildTrackerHandler
from core.database.handlers.guild import GuildSnapshot


class GuildSnapshots(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.guild_snapshot_task.start()

    def cog_unload(self) -> None:
        self.guild_snapshot_task.cancel()

    @tasks.loop(minutes=5)
    async def guild_snapshot_task(self) -> None:
        handler = GuildTrackerHandler()
        guilds = handler.get_tracked_guilds()
        today = datetime.date.today()

        for guild in guilds:
            guild_info = await GuildInfo.fetch(guild.guild_id)

            if not guild_info:
                continue

            handler.add_snapshot(
                GuildSnapshot(
                    id=None,
                    guild_id=guild.guild_id,
                    gxp=guild_info.xp,
                    date=today,
                )
            )

    @guild_snapshot_task.before_loop
    async def before_guild_snapshot_task(self) -> None:
        await self.client.wait_until_ready()


async def setup(client: commands.Bot) -> None:
    await client.add_cog(GuildSnapshots(client))
