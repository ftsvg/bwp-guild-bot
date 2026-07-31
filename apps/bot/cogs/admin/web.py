from discord import Interaction, User, app_commands
from discord.ext import commands
from discord.ui import Button, View

from core.api import mojang_client
from core.database.handlers.web import WebUserHandler

ROLE_CHOICES = [
    app_commands.Choice(name="User", value=0),
    app_commands.Choice(name="Admin", value=1),
]


class Web(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client

    web = app_commands.Group(
        name="web",
        description="Web related commands",
    )

    @web.command(
        name="grant",
        description="Allow a new user to the website.",
    )
    @app_commands.describe(
        user="The user you want to give access to.",
        player="The users minecraft username.",
        role="The users permissions role.",
    )
    @app_commands.choices(role=ROLE_CHOICES)
    async def grant(
        self,
        interaction: Interaction,
        user: User,
        player: str,
        role: app_commands.Choice[int],
    ):
        await interaction.response.defer(ephemeral=True)

        if not interaction.user.guild_permissions.administrator:
            return await interaction.edit_original_response(
                content="You do not have the permissions to execute this command."
            )

        uuid = await mojang_client.get_uuid(player)
        if not uuid:
            return await interaction.edit_original_response(
                content=(
                    f"**{player}** does not exist. Make sure to enter a valid username."
                )
            )

        handler = WebUserHandler(discord_id=user.id)

        created = handler.create_user(
            uuid=uuid,
            role=role.value,
        )

        if not created:
            return await interaction.edit_original_response(
                content=f"**{user.name}** is already whitelisted."
            )

        await interaction.edit_original_response(
            content=f"Successfully whitelisted **{user.name}**."
        )

    @web.command(
        name="revoke",
        description="Remove a user's website access.",
    )
    @app_commands.describe(
        user="The user you want to remove access from.",
    )
    async def revoke(
        self,
        interaction: Interaction,
        user: User,
    ):
        await interaction.response.defer(ephemeral=True)

        if not interaction.user.guild_permissions.administrator:
            return await interaction.edit_original_response(
                content="You do not have the permissions to execute this command."
            )

        handler = WebUserHandler(discord_id=user.id)

        deleted = handler.delete_user()

        if not deleted:
            return await interaction.edit_original_response(
                content=f"**{user.name}** is not whitelisted."
            )

        await interaction.edit_original_response(
            content=f"Successfully revoked access from **{user.name}**."
        )

    @web.command(
        name="login",
        description="Login to the website",
    )
    async def login(
        self,
        interaction: Interaction,
    ):
        await interaction.response.defer(ephemeral=True)

        handler = WebUserHandler(discord_id=interaction.user.id)
        link = handler.create_magic_link(
            base_url="http://127.0.0.1:5000/login",
            lifetime=300,
        )

        if link is None:
            return await interaction.edit_original_response(
                content="You do not have the permissions to execute this command."
            )

        await interaction.edit_original_response(
            content=(
                "Welcome, click the button below to login.\n"
                "- This link expires in `5` minutes."
            ),
            view=LoginButton(link),
        )


class LoginButton(View):
    def __init__(self, url: str):
        super().__init__(timeout=300)

        self.add_item(
            Button(
                label="Login",
                url=url,
            )
        )


async def setup(client: commands.Bot):
    await client.add_cog(Web(client))
