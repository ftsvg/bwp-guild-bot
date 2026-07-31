from discord import AllowedMentions, Interaction, app_commands
from discord.ext import commands

from core.api import mojang_client
from core.database.handlers import (
    SettingsHandler,
    VerifyHandler,
    VerifyRequestHandler,
)
from core.ui.components import VerificationComponent


class verification(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(
        name="verify",
        description="Link your Minecraft account with your Discord account.",
    )
    @app_commands.describe(player="The account you want to verify with.")
    async def verify(self, interaction: Interaction, player: str):
        verify_handler = VerifyHandler(interaction.user.id)

        user = verify_handler.get_verified_user()

        if user and user.uuid:
            return await interaction.response.send_message(
                content=(
                    "You are already verified. Want to verify with a new "
                    "account? Run **/unverify** and then run **/verify** again"
                ),
                ephemeral=True,
            )

        pending = VerifyRequestHandler().get_by_discord_id(interaction.user.id)

        if pending:
            return await interaction.response.send_message(
                content="You already have a verification pending.",
                ephemeral=True,
            )

        uuid = await mojang_client.get_uuid(player)

        if not uuid:
            return await interaction.response.send_message(
                content=f"**{player}** does not exist, please enter a valid ign."
            )

        player_name = await mojang_client.get_username(uuid)

        settings = SettingsHandler(interaction.guild.id).get_settings()

        if not settings.verification:
            return await interaction.response.send_message(
                content="No verification requests channel has been set.",
                ephemeral=True,
            )

        channel = await interaction.client.fetch_channel(settings.verification)

        message = await channel.send(
            view=VerificationComponent(
                interaction.user,
                uuid,
                player_name,
            ),
            allowed_mentions=AllowedMentions.none(),
        )

        VerifyRequestHandler(message.id).create(
            discord_id=interaction.user.id,
            uuid=uuid,
        )

        return await interaction.response.send_message(
            content=(
                "You have successfully submitted a verification request. "
                "A staff member will review and accept your request "
                "as soon as possible."
            ),
            ephemeral=True,
        )


async def setup(client: commands.Bot) -> None:
    await client.add_cog(verification(client))
