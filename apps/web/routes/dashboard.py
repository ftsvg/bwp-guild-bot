from quart import Blueprint, render_template, session

from apps.web.utils import login_required
from core.api import mojang_client
from core.api.helpers import GuildInfo
from core.database.handlers import GuildTrackerHandler, WebUserHandler
from core.services import GuildService, TrackedGuildService

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
async def dashboard():

    user_id = session.get("user_id")

    user = WebUserHandler().get_user_by_id(user_id)
    user.username = await mojang_client.get_username(user.uuid)

    tracked_guilds = await TrackedGuildService.get_top_guilds(10)

    guild_info = await GuildInfo.fetch(766)
    guild = GuildService(guild_info).get_stats()

    guild_logs = GuildTrackerHandler().get_logs(guild_id=766, limit=5)

    return await render_template(
        "dashboard.html",
        user=user,
        guild=guild,
        tracked_guilds=tracked_guilds,
        guild_logs=guild_logs,
    )
