from discord import ButtonStyle, Interaction
from discord.ui import Button

from core.database.handlers import VerifyHandler, VerifyRequestHandler


class AcceptButton(Button):
    def __init__(self):
        super().__init__(
            label="Accept",
            style=ButtonStyle.green,
            custom_id="verify_accept",
        )

    async def callback(self, interaction: Interaction):
        request = VerifyRequestHandler(interaction.message.id).get()

        if request is None:
            return await interaction.response.send_message(
                "This verification request no longer exists.",
                ephemeral=True,
            )

        await VerifyHandler(request.discord_id).verify_user(request.uuid)

        VerifyRequestHandler(interaction.message.id).delete()

        await interaction.message.delete()


class DenyButton(Button):
    def __init__(self):
        super().__init__(
            label="Deny",
            style=ButtonStyle.red,
            custom_id="verify_deny",
        )

    async def callback(self, interaction: Interaction):
        request = VerifyRequestHandler(interaction.message.id).get()

        if request is None:
            return await interaction.response.send_message(
                "This verification request no longer exists.",
                ephemeral=True,
            )

        VerifyRequestHandler(interaction.message.id).delete()

        await interaction.message.delete()
