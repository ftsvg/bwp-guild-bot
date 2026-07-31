from discord import ChannelType, Guild, Interaction
from discord.ui import ChannelSelect, RoleSelect

from core.database.handlers import SettingsHandler, SettingType


class SettingChannelSelect(ChannelSelect):
    def __init__(self, guild: Guild, setting: SettingType):
        super().__init__(
            placeholder="Select a text channel...",
            channel_types=[
                ChannelType.text,
                ChannelType.news,
            ],
        )

        self.guild = guild
        self.setting = setting

    async def callback(self, interaction: Interaction):
        channel = self.values[0]

        SettingsHandler(self.guild.id).set_setting(self.setting, channel.id)

        from core.ui.components import SettingsComponent

        await interaction.response.edit_message(view=SettingsComponent(self.guild))


class SettingRoleSelect(RoleSelect):
    def __init__(self, guild: Guild, setting: SettingType):
        super().__init__(placeholder="Select a role...")

        self.guild = guild
        self.setting = setting

    async def callback(self, interaction: Interaction):
        role = self.values[0]

        SettingsHandler(self.guild.id).set_setting(self.setting, role.id)

        from core.ui.components import SettingsComponent

        await interaction.response.edit_message(view=SettingsComponent(self.guild))
