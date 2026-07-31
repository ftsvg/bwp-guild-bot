from discord.ui import View


class VerificationView(View):
    def __init__(self):
        super().__init__(timeout=None)

        from ..buttons.verify import AcceptButton, DenyButton

        self.add_item(AcceptButton())
        self.add_item(DenyButton())
