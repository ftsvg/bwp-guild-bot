from typing import Literal

from discord import Guild
from discord.ui import (
    ActionRow,
    Container,
    LayoutView,
    Section,
    Separator,
    TextDisplay,
)

from core.database.handlers import SettingsHandler, SettingType
from core.ui.buttons import BackButton, SettingButton
from core.ui.dropdowns import SettingChannelSelect, SettingRoleSelect

SETTING_INFO: dict[SettingType, tuple[str, str, Literal["channel", "role"]]] = {
    "verification": (
        "Verify Requests Channel",
        "Channel where verification requests get sent to.",
        "channel",
    ),
    "applications": (
        "Applications Channel",
        "Channel where new guild applications get sent to.",
        "channel",
    ),
    "charts": (
        "XP Charts Channel",
        "Channel where XP/GXP charts get sent to.",
        "channel",
    ),
    "gxp_updates": (
        "GXP Updates Channel",
        "Channel where GXP updates get sent to.",
        "channel",
    ),
    "streak": (
        "Daily Streak Channel",
        "Channel where people can start a streak.",
        "channel",
    ),
    "counting": (
        "Counting Channel",
        "Channel where people can start counting.",
        "channel",
    ),
    "lactate": ("Lactate Channel", "Channel where people can lactate.", "channel"),
    "guild_role": (
        "Guild Member Role",
        "Role given to guild members when they successfully verify",
        "role",
    ),
}


class SettingsComponent(LayoutView):
    def __init__(self, guild: Guild):
        super().__init__(timeout=None)

        settings = SettingsHandler(guild.id).get_settings()
        container = Container()

        container.add_item(
            TextDisplay(
                "## Settings\nManage this server's guild tracking configuration."
            )
        )
        container.add_item(Separator())

        for setting, (title, description, _) in SETTING_INFO.items():
            value = getattr(settings, setting)

            current = "`Not set`"

            if value:
                if setting == "guild_role":
                    role = guild.get_role(value)
                    if role:
                        current = role.mention
                else:
                    channel = guild.get_channel(value)
                    if channel:
                        current = channel.mention

            container.add_item(
                Section(
                    TextDisplay(f"**{title}**: {current}\n-# {description}"),
                    accessory=SettingButton(guild, setting),
                )
            )
        self.add_item(container)


class SettingEditComponent(LayoutView):
    def __init__(self, guild: Guild, setting: SettingType):
        super().__init__(timeout=None)

        self.guild = guild
        self.setting = setting

        title, description, kind = SETTING_INFO[setting]

        container = Container()

        container.add_item(TextDisplay(f"## {title}\n-# {description}"))

        if kind == "channel":
            container.add_item(ActionRow(SettingChannelSelect(guild, setting)))
        else:
            container.add_item(ActionRow(SettingRoleSelect(guild, setting)))

        container.add_item(ActionRow(BackButton(guild)))
        self.add_item(container)
