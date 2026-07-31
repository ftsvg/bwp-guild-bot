from discord import ButtonStyle, Guild, Interaction
from discord.ui import (
    Button,
)

from core.database.handlers import SettingType


class SettingButton(Button):
    def __init__(self, guild: Guild, setting: SettingType):
        super().__init__(label="Edit", style=ButtonStyle.gray)

        self.guild = guild
        self.setting = setting

    async def callback(self, interaction: Interaction):
        from core.ui.components import SettingEditComponent

        await interaction.response.edit_message(
            view=SettingEditComponent(self.guild, self.setting)
        )


class BackButton(Button):
    def __init__(self, guild: Guild):
        super().__init__(label="Back", style=ButtonStyle.blurple)
        self.guild = guild

    async def callback(self, interaction: Interaction):
        from core.ui.components import SettingsComponent

        await interaction.response.edit_message(view=SettingsComponent(self.guild))
