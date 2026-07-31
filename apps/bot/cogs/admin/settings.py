from discord import Interaction, app_commands
from discord.ext import commands

from core.ui.components import SettingsComponent


class Settings(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name="settings", description="Configure the server settings")
    async def settings(self, interaction: Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                content="You do not have the permissions to execute this command.",
                ephemeral=True,
            )

        await interaction.response.send_message(
            view=SettingsComponent(interaction.guild), ephemeral=True
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Settings(client))
