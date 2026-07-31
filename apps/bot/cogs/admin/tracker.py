from datetime import date

from discord import Interaction, TextChannel, app_commands
from discord.ext import commands

from core.api.helpers import GuildInfo
from core.database.handlers import GuildTrackerHandler
from core.database.handlers.guild import GuildSnapshot, TrackedGuild


class GuildTracker(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client

    tracker = app_commands.Group(name="tracker", description="Tracker related commands")

    @tracker.command(name="add", description="Add a guild to the tracker")
    @app_commands.describe(
        tag="The guild you want to track.",
        logs_channel="The channel where join/leave logs get sent to.",
    )
    async def tracker_add(
        self, interaction: Interaction, tag: str, logs_channel: TextChannel
    ):
        await interaction.response.defer()
        if not interaction.user.guild_permissions.administrator:
            return await interaction.edit_original_response(
                content="You do not have the permissions to execute this command."
            )

        guild_info = await GuildInfo.fetch(tag)
        if not guild_info:
            return await interaction.edit_original_response(
                content="Guild not found. Please enter a valid guild tag and try again."
            )

        guild_id = guild_info.id
        guild_handler = GuildTrackerHandler()

        is_tracked = guild_handler.get_guild(guild_id)
        if is_tracked:
            return await interaction.edit_original_response(
                content="You are already tracking this guild."
            )

        guild_handler.add_guild(TrackedGuild(guild_id, logs_channel.id))
        guild_handler.add_snapshot(
            GuildSnapshot(None, guild_id, guild_info.xp, date.today())
        )

        await guild_handler.track_players(
            guild_info,
            guild_id,
        )

        return await interaction.edit_original_response(
            content=(
                f"**{guild_info.name} [{tag.upper()}] ({guild_id})** "
                "has been added successfully and will now be tracked."
            )
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(GuildTracker(client))
