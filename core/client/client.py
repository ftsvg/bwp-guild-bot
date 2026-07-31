from pathlib import Path

from discord import Intents
from discord.ext import commands

from core import logger
from core.api import mojang_client, voxyl_client
from core.ui.views import VerificationView

intents = Intents.default()
intents.message_content = True


class Client(commands.AutoShardedBot):
    def __init__(self, *, intents: Intents = intents):
        super().__init__(
            intents=intents,
            command_prefix=commands.when_mentioned_or("$"),
        )

    async def setup_hook(self) -> None:
        await voxyl_client.start()
        await mojang_client.start()

        for file in Path("apps/bot/cogs").rglob("*.py"):
            module = ".".join(file.with_suffix("").parts)

            try:
                await self.load_extension(module)
                logger.info(f"Loaded: {module}")

            except Exception as error:
                logger.exception(f"Failed to load {module}: {error}")

        self.add_view(VerificationView())

    async def close(self):
        await voxyl_client.close()
        await mojang_client.close()

        await super().close()

    async def on_ready(self) -> None:
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
