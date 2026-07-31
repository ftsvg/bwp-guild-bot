from discord import User
from discord.ui import (
    ActionRow,
    Container,
    LayoutView,
    Separator,
    TextDisplay,
)

from core.ui.buttons import AcceptButton, DenyButton


class VerificationComponent(LayoutView):
    def __init__(self, user: User, uuid: str, player_name: str):
        super().__init__(timeout=None)

        container = Container()
        container.add_item(TextDisplay("## Verification Request Submitted"))
        container.add_item(Separator())
        container.add_item(
            TextDisplay(
                (
                    "- **Submitted by:**\n"
                    f"  - Member: {user.mention}\n"
                    f"  - ID: `{user.id}`\n"
                    "- **Requested account:**\n"
                    f"  - Username: `{player_name}`\n"
                    f"  - UUID: `{uuid}`"
                )
            )
        )
        container.add_item(Separator())
        container.add_item(
            ActionRow(
                AcceptButton(),
                DenyButton(),
            )
        )

        self.add_item(container)
